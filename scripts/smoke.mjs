import assert from 'node:assert/strict';

const base = process.env.API_URL ?? 'http://127.0.0.1:3000/api';
const request = (path, body) => fetch(`${base}${path}`, {
  ...(body !== undefined ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}),
  signal: AbortSignal.timeout(15_000)
});
async function json(path, body) {
  const response = await request(path, body);
  assert.ok(response.ok, `${path}: ${response.status} ${response.statusText}`);
  return response.json();
}
async function settled(id) {
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    const task = await json(`/analyses/${id}`);
    if (task.status !== 'running') return task;
    await new Promise((resolve) => setTimeout(resolve, 30));
  }
  throw new Error(`Task ${id} did not settle`);
}
async function* events(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true }).replaceAll('\r\n', '\n');
      let boundary;
      while ((boundary = buffer.indexOf('\n\n')) >= 0) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const payload = block.split('\n').filter((line) => line.startsWith('data:')).map((line) => line.slice(5).trimStart()).join('\n');
        if (payload) yield JSON.parse(payload);
      }
    }
  } finally { await reader.cancel(); }
}

const claims = await json('/cases');
assert.equal(claims.length, 2);
assert.equal((await request('/analyses', {})).status, 400);
assert.equal((await request('/analyses', { caseId: 'UNKNOWN' })).status, 404);
assert.equal((await request('/analyses/unknown')).status, 404);

const risky = await json('/analyses', { caseId: claims[0].id });
const waiting = await settled(risky.id);
assert.equal(waiting.status, 'waiting_review');
assert.equal(waiting.report, undefined);
assert.equal(waiting.findings.length, 2);
assert.equal(waiting.citations.length, 2);
assert.equal((await request(`/analyses/${risky.id}/review`, { decision: 'invalid' })).status, 400);

// Connect after the persisted review request, then verify live resume/report events.
const cursor = waiting.events.at(-1).id;
const stream = await fetch(`${base}/analyses/${risky.id}/events`, {
  headers: { 'Last-Event-ID': String(cursor) }, signal: AbortSignal.timeout(15_000)
});
assert.match(stream.headers.get('content-type'), /text\/event-stream/);
await json(`/analyses/${risky.id}/review`, { decision: 'approve', comment: '冒烟验证：继续分析' });
const received = [];
for await (const event of events(stream)) received.push(event);
assert.deepEqual(received.map((event) => event.id), [cursor + 1, cursor + 2]);
assert.equal(received.at(-1).type, 'report');
assert.equal(received.at(-1).status, 'completed');
const completed = await json(`/analyses/${risky.id}`);
assert.equal(completed.report.reviewerComment, '冒烟验证：继续分析');
assert.equal(completed.events.filter((event) => event.type === 'review_required').length, 1);
assert.equal((await request(`/analyses/${risky.id}/review`, { decision: 'approve' })).status, 409);

const rejected = await json('/analyses', { caseId: claims[0].id });
await settled(rejected.id);
await json(`/analyses/${rejected.id}/review`, { decision: 'reject', comment: '先补材料' });
assert.equal((await json(`/analyses/${rejected.id}`)).status, 'rejected');

const normal = await json('/analyses', { caseId: claims[1].id });
const normalResult = await settled(normal.id);
assert.equal(normalResult.status, 'completed');
assert.equal(normalResult.report.citations.length, 1);
assert.ok((await json('/analyses')).some((task) => task.id === risky.id));
console.log('PASS: HTTP validation, review pause/resume/rejection, duplicate-review guard, clean case, SSE live delivery and cursor replay.');

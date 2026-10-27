import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from '../../../apps/web/node_modules/vite/dist/node/index.js';
import { createRenderer } from '../../../apps/web/node_modules/vue/index.mjs';

// Vite resolves application TS imports exactly as in the browser. Vue's custom
// renderer exercises actual mount/unmount hooks without requiring a DOM shim.
const server = await createServer({ configFile: false, root: fileURLToPath(new URL('../../../apps/web', import.meta.url)), server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom', optimizeDeps: { noDiscovery: true, include: [] } });
after(async () => { await server.close(); });
const { useKnowledge } = await server.ssrLoadModule('/src/composables/useKnowledge.ts');
const { knowledgeApi } = await server.ssrLoadModule('/src/api/knowledge.ts');
const { ApiError } = await server.ssrLoadModule('/src/api/http.ts');
const renderer = createRenderer({
  createElement: () => ({}), createText: () => ({}), createComment: () => ({}),
  insert() {}, remove() {}, setText() {}, setElementText() {}, patchProp() {},
  parentNode: () => null, nextSibling: () => null,
});

const generation = (id: string) => ({
  generationId: id, documentId: `document-${id}`, productCode: 'AUTO-COMPREHENSIVE', clauseVersion: '2025-01',
  fileName: `${id}.pdf`, sha256: 'a'.repeat(64), status: 'embedding', revision: 3, attempt: 1,
  pageCount: 2, chunkCount: 4, embeddedCount: 1, isActive: false, error: null,
  createdAt: '2026-10-23T01:00:00.000Z', updatedAt: '2026-10-23T01:00:02.000Z', attempts: [],
});
const deferred = () => {
  let resolve!: (value: unknown) => void;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
};
async function mount() {
  knowledgeApi.list = async () => [];
  let state: ReturnType<typeof useKnowledge>;
  const app = renderer.createApp({ setup() { state = useKnowledge(); return () => null; } });
  app.mount({});
  await new Promise(done => setImmediate(done));
  return { app, state: state! };
}

test('late progress from generation A cannot overwrite a newly selected generation B', async () => {
  const { app, state } = await mount();
  const delayed = deferred();
  const a = generation('a');
  const b = generation('b');
  knowledgeApi.generation = (id: string) => id === 'a' ? delayed.promise : Promise.resolve(b);
  try {
    const first = state.select(a);
    await state.select(b);
    delayed.resolve({ ...a, embeddedCount: 4 });
    await first;
    assert.equal(state.selected.value.generationId, 'b');
    assert.equal(state.selected.value.embeddedCount, 1);
  } finally { app.unmount(); }
});

test('pausing or leaving ignores in-flight progress even when transport ignores cancellation', async () => {
  for (const stop of ['pause', 'unmount']) {
    const { app, state } = await mount();
    const delayed = deferred();
    const a = generation('a');
    knowledgeApi.generation = () => delayed.promise;
    const reading = state.select(a);
    if (stop === 'pause') state.pause(); else app.unmount();
    delayed.resolve({ ...a, embeddedCount: 4, status: 'ready' });
    await reading;
    assert.equal(state.selected.value.embeddedCount, 1);
    assert.equal(state.polling.value, false);
    if (stop === 'pause') app.unmount();
  }
});

test('retrying an uncertain submission reuses its idempotency key and revision', async () => {
  const { app, state } = await mount();
  const failed = { ...generation('failed'), status: 'failed' };
  const accepted = { ...failed, status: 'queued', revision: 4 };
  const calls: { revision: number; key: string }[] = [];
  knowledgeApi.generation = async () => accepted;
  knowledgeApi.retry = async (_id: string, revision: number, key: string) => {
    calls.push({ revision, key });
    if (calls.length === 1) throw new ApiError(0, 'connection lost');
    return accepted;
  };
  state.selected.value = failed;
  try {
    await state.retry();
    assert.equal(state.selected.value.status, 'failed');
    await state.retry();
    assert.equal(calls.length, 2);
    assert.deepEqual(calls[0], calls[1]);
    assert.equal(calls[0].revision, 3);
    assert.equal(state.selected.value.revision, 4);
  } finally { app.unmount(); }
});

test('a publication conflict refreshes the expected generation and requires new confirmation', async () => {
  const { app, state } = await mount();
  const previous = { ...generation('old'), status: 'ready', isActive: true };
  const current = { ...generation('new'), status: 'ready', isActive: true };
  state.generations.value = [previous];
  state.chooseFile(new File(['sample'], 'clauses.pdf', { type: 'application/pdf' }));
  await new Promise(done => setImmediate(done));
  state.confirmed.value = true;
  knowledgeApi.upload = async (body: FormData) => {
    assert.equal(body.get('expectedGenerationId'), 'old');
    throw new ApiError(409, '发布版本已变化', 'GENERATION_CONFLICT');
  };
  knowledgeApi.list = async () => [current, { ...previous, isActive: false }];
  try {
    await state.upload();
    assert.equal(state.publication.value.generationId, 'new');
    assert.equal(state.confirmed.value, false);
    assert.match(state.error.value, /发布版本已变化/);
  } finally { app.unmount(); }
});

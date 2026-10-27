import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from '../../../apps/web/node_modules/vite/dist/node/index.js';
import { createRenderer } from '../../../apps/web/node_modules/vue/index.mjs';

const server = await createServer({ configFile: false, root: fileURLToPath(new URL('../../../apps/web', import.meta.url)), server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom', optimizeDeps: { noDiscovery: true, include: [] } });
after(async () => { await server.close(); });
const { useWorkbench } = await server.ssrLoadModule('/src/composables/useWorkbench.ts');
const { workbenchApi } = await server.ssrLoadModule('/src/api/workbench.ts');
const { ApiError } = await server.ssrLoadModule('/src/api/http.ts');
class Source {
  static instances: Source[] = [];
  listeners = new Map<string, (message: unknown) => void>();
  onopen?: () => void; onerror?: () => void; closed = false;
  constructor(readonly url: string) { Source.instances.push(this); }
  addEventListener(name: string, callback: (message: unknown) => void) { this.listeners.set(name, callback); }
  close() { this.closed = true; }
}
Object.defineProperty(globalThis, 'EventSource', { value: Source, configurable: true });
const renderer = createRenderer({ createElement: () => ({}), createText: () => ({}), createComment: () => ({}), insert() {}, remove() {}, setText() {}, setElementText() {}, patchProp() {}, parentNode: () => null, nextSibling: () => null });
const turn = (id: string) => ({ schemaVersion: 1, id, caseId: 'CASE-2026-001', conversationId: `conversation-${id}`, kind: 'initial', question: '核验', status: 'running', revision: 2, lastEventSeq: 2, userMessageId: `user-${id}`, assistantMessageId: null, caseSnapshot: { id: 'CASE-2026-001', claimant: '演示', materials: [] }, context: { messageIds: [] }, facts: [], ruleFindings: [], modelFindings: [], citations: [], sections: [], report: null, pendingReview: null, execution: { nodes: [], tools: [], timeline: [] }, error: null });
const conversation = (id: string) => ({ id, caseId: 'CASE-2026-001', title: '验收', messages: [], analysisIds: [], activeAnalysisId: null, nextBefore: null });
const citationContext = (id: string) => ({
  citation: { citationId: id, chunkId: `chunk-${id}`, generationId: 'generation-a', documentId: 'document-a', fileName: '条款.pdf', productCode: 'AUTO', clauseVersion: '2025-01', page: 1, ordinal: 0, content: `引用 ${id}` },
  previous: null,
  next: null,
});
const tick = () => new Promise(done => setImmediate(done));
function deferred() { let resolve!: (value: unknown) => void; let reject!: (value: unknown) => void; const promise = new Promise((done, fail) => { resolve = done; reject = fail; }); return { promise, resolve, reject }; }
async function mount(initialHistory = []) {
  Source.instances = [];
  workbenchApi.cases = async () => [];
  workbenchApi.history = async () => initialHistory;
  workbenchApi.conversations = async () => [];
  workbenchApi.conversation = async (id: string) => conversation(id);
  workbenchApi.task = async (id: string) => turn(id);
  let state: ReturnType<typeof useWorkbench>;
  const app = renderer.createApp({ setup() { state = useWorkbench(); return () => null; } });
  app.mount({}); await tick();
  return { app, state: state! };
}

test('late task HTTP results and stale SSE callbacks cannot overwrite another selection', async () => {
  const { app, state } = await mount();
  try {
    await state.openTask('a');
    const old = Source.instances.at(-1)!;
    const delayed = deferred();
    workbenchApi.task = (id: string) => id === 'slow' ? delayed.promise : Promise.resolve(turn(id));
    const loading = state.openTask('slow');
    await state.openTask('b');
    const current = Source.instances.at(-1)!;
    current.onopen?.();
    old.listeners.get('timeline')?.({ data: 'invalid JSON' });
    old.onerror?.();
    delayed.reject(new Error('late failure'));
    await loading;
    assert.equal(state.task.value.id, 'b');
    assert.equal(state.pending.value, false);
    assert.equal(state.error.value, '');
    assert.equal(state.connection.value, '实时连接');
    assert.equal(current.closed, false);
    assert.match(current.url, /after=2$/);
  } finally { app.unmount(); }
});

test('uncertain initial submission preserves the question, conversation and idempotency key', async () => {
  const { app, state } = await mount();
  const calls: unknown[] = [];
  let creations = 0;
  workbenchApi.createConversation = async () => { creations++; return conversation('new-conversation'); };
  workbenchApi.start = async (body: unknown, key: string) => {
    calls.push({ body, key });
    if (calls.length === 1) throw new ApiError(0, 'response lost');
    return { ...turn('created'), conversationId: 'new-conversation', status: 'waiting_review' };
  };
  try {
    state.question.value = '保留我的原问题';
    await state.start(false);
    assert.match(state.error.value, /response lost/);
    assert.equal(state.question.value, '保留我的原问题');
    await state.start(false);
    assert.equal(creations, 1);
    assert.deepEqual(calls[0], calls[1]);
    assert.equal(state.task.value.id, 'created');
  } finally { app.unmount(); }
});

test('review conflicts resynchronize the authoritative snapshot without guessing approval', async () => {
  const { app, state } = await mount();
  try {
    state.task.value = { ...turn('review'), status: 'waiting_review', pendingReview: { interruptKey: 'i1', checkpointId: 'cp1', revision: 2, reason: '核验' } };
    workbenchApi.review = async () => { throw new ApiError(409, '审核点已变化'); };
    workbenchApi.task = async () => ({ ...turn('review'), status: 'rejected', revision: 4, lastEventSeq: 4 });
    await state.review('approve');
    assert.equal(state.task.value.status, 'rejected');
    assert.equal(state.task.value.revision, 4);
    assert.match(state.error.value, /审核点已变化/);
  } finally { app.unmount(); }
});

test('a slower earlier citation response cannot replace the latest selected citation', async () => {
  const { app, state } = await mount();
  const delayed = deferred();
  state.task.value = turn('citations');
  workbenchApi.citation = async (_taskId: string, citationId: string) => citationId === 'citation-a'
    ? delayed.promise
    : citationContext(citationId);
  try {
    const first = state.showCitation('citation-a');
    const second = state.showCitation('citation-b');
    await second;
    assert.equal(state.citation.value.citation.citationId, 'citation-b');
    delayed.resolve(citationContext('citation-a'));
    await first;
    assert.equal(state.citation.value.citation.citationId, 'citation-b');
  } finally { app.unmount(); }
});

test('stream errors reopen from a fresh snapshot and unmount invalidates callbacks', async () => {
  const { app, state } = await mount();
  await state.openTask('a');
  const first = Source.instances.at(-1)!;
  workbenchApi.task = async () => ({ ...turn('a'), revision: 5, lastEventSeq: 5 });
  first.onerror?.();
  await tick();
  assert.equal(first.closed, true);
  assert.match(Source.instances.at(-1)!.url, /after=5$/);
  app.unmount();
  const count = Source.instances.length;
  first.onerror?.();
  await tick();
  assert.equal(Source.instances.length, count);
});

test('asking the same question after confirmed completion creates a new turn key', async () => {
  const { app, state } = await mount();
  const keys: string[] = [];
  const completedConversation = { ...conversation('same'), messages: [{ role: 'assistant', id: 'previous', content: '已完成' }] };
  state.conversation.value = completedConversation;
  workbenchApi.conversation = async () => completedConversation;
  workbenchApi.start = async (_body: unknown, key: string) => { keys.push(key); return { ...turn(`repeat-${keys.length}`), conversationId: 'same', status: 'completed' }; };
  try {
    state.question.value = '相同问题'; await state.start(false);
    state.question.value = '相同问题'; await state.start(false);
    assert.equal(keys.length, 2);
    assert.notEqual(keys[0], keys[1]);
    assert.equal(state.task.value.id, 'repeat-2');
  } finally { app.unmount(); }
});

test('a refreshed page restores its saved task from the server before opening a stream', async () => {
  const values = new Map([['casepilot:last-task', 'saved']]);
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: { getItem: (key: string) => values.get(key) ?? null, setItem: (key: string, value: string) => values.set(key, value) } });
  const { app, state } = await mount([turn('saved')]);
  try {
    await tick();
    assert.equal(state.task.value.id, 'saved');
    assert.match(Source.instances.at(-1)!.url, /analyses\/saved\/events\?after=2$/);
  } finally { app.unmount(); delete globalThis.localStorage; }
});

test('late history pagination preserves messages arriving during the request', async () => {
  const { app, state } = await mount();
  const delayed = deferred();
  state.conversation.value = { ...conversation('history'), messages: [{ id: 'recent', role: 'user' }], nextBefore: 'recent' };
  workbenchApi.conversation = async () => delayed.promise;
  try {
    const loading = state.olderMessages();
    state.conversation.value = { ...state.conversation.value, messages: [...state.conversation.value.messages, { id: 'arriving', role: 'assistant' }] };
    delayed.resolve({ ...conversation('history'), messages: [{ id: 'older', role: 'user' }], nextBefore: null });
    await loading;
    assert.deepEqual(state.conversation.value.messages.map(m => m.id), ['older', 'recent', 'arriving']);
    assert.equal(state.conversation.value.nextBefore, null);
  } finally { app.unmount(); }
});

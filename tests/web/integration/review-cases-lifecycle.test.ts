import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from '../../../apps/web/node_modules/vite/dist/node/index.js';
import { createRenderer } from '../../../apps/web/node_modules/vue/index.mjs';

const server = await createServer({ configFile: false, root: fileURLToPath(new URL('../../../apps/web', import.meta.url)), server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom', optimizeDeps: { noDiscovery: true, include: [] } });
after(async () => { await server.close(); });
const { useReviewCases } = await server.ssrLoadModule('/src/composables/useReviewCases.ts');
const { reviewCasesApi } = await server.ssrLoadModule('/src/api/reviewCases.ts');
const renderer = createRenderer({ createElement: () => ({}), createText: () => ({}), createComment: () => ({}), insert() {}, remove() {}, setText() {}, setElementText() {}, patchProp() {}, parentNode: () => null, nextSibling: () => null });
const summary = (id: string) => ({ id, revision: 1, targetClaims: [{ claimId: `claim-${id}`, claimNumber: id, reportNumber: `report-${id}`, scopeRole: 'target', closureType: 'paid_closed', closedAt: '2026-01-02T00:00:00+08:00', originalPaymentStatus: 'settled' }], relatedClaims: [], vehicles: [], accidentAt: '2026-01-01T00:00:00+08:00', originalApprovedAmount: { status: 'known', amountFen: 100, currency: 'CNY', reason: null }, effectivePaidAmount: { status: 'known', amountFen: 100, currency: 'CNY', reason: null }, injuryStatus: 'no_injury_reported', latestReviewStatus: 'not_started' });
const tick = () => new Promise(done => setImmediate(done));
function deferred() { let resolve!: (value: unknown) => void; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; }

async function mount() {
  reviewCasesApi.list = async () => ({ dataStatus: 'ready', items: [summary('C01'), summary('C02')] });
  let state: ReturnType<typeof useReviewCases>;
  const app = renderer.createApp({ setup() { state = useReviewCases(); return () => null; } });
  app.mount({}); await tick(); await tick();
  return { app, state: state! };
}

test('a slower earlier case query cannot replace the latest result', async () => {
  const { app, state } = await mount();
  try {
    const slow = deferred();
    let calls = 0;
    reviewCasesApi.list = () => ++calls === 1 ? slow.promise : Promise.resolve({ dataStatus: 'ready', items: [summary('C02')] });
    const first = state.search();
    await tick();
    state.filters.query = 'C02';
    await state.search();
    slow.resolve({ dataStatus: 'ready', items: [summary('C01')] });
    await first;
    assert.equal(state.selectedId.value, 'C02');
    assert.deepEqual(state.cases.value.map((item: { id: string }) => item.id), ['C02']);
    assert.equal(state.pending.value, false);
  } finally { app.unmount(); }
});

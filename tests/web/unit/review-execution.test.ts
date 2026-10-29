import assert from 'node:assert/strict';
import { test } from 'node:test';
import { executionGroups, nodeNames, unresolved } from '../../../apps/web/src/domain/reviewExecution.ts';
import type { AnalysisTask } from '../../../packages/contracts/dist/workspace.js';

const task = (patch = {}) => ({ status: 'waiting_review', reviewHistory: [],
  finalizationEligibility: { allowed: false, blockers: ['必要检查无法执行'], basisHash: 'fixed' },
  reviewState: { checks: [], findings: [], records: [], businessNodes: Object.keys(nodeNames).map(nodeKey => ({ nodeKey, status: 'not_started' })) },
  execution: { tools: [], timeline: [] }, ...patch }) as unknown as AnalysisTask;

test('human decisions and report versions appear at their owning business node', () => {
  const current = task({ execution: { tools: [], timeline: [
    { type: 'finding.reviewed', data: { review: { nodeKey: 'amount', findingId: 'payment' } } },
    { type: 'report.saved', data: { version: 1 } },
    { type: 'evidence.supplemented', data: { supplement: { nodeKey: 'consistency' } } },
  ] } });
  const groups = executionGroups(current);
  assert.equal(groups.find(g => g.key === 'amount')?.events[0].type, 'finding.reviewed');
  assert.equal(groups.find(g => g.key === 'report')?.events[0].type, 'report.saved');
  assert.equal(groups.find(g => g.key === 'consistency')?.events[0].type, 'evidence.supplemented');
  assert.equal(groups.find(g => g.key === 'coverage')?.status, '未开始');
});

test('client does not infer completion from a decision or uploaded attachment', () => {
  const current = task({ reviewHistory: [{ findingId: 'gap', decision: 'excluded', supplementIds: ['new-pdf'] }] });
  assert.deepEqual(unresolved(current), ['必要检查无法执行']);
  const accepted = task({ finalizationEligibility: { allowed: true, blockers: [], basisHash: 'fixed' } });
  assert.deepEqual(unresolved(accepted), []);
});

test('finding review status does not replace a failed automatic node status', () => {
  const current = task();
  current.reviewState.businessNodes.find(n => n.nodeKey === 'amount')!.status = 'failed';
  current.reviewHistory = [{ findingId: 'payment', nodeKey: 'amount', decision: 'confirmed' }] as AnalysisTask['reviewHistory'];
  assert.equal(executionGroups(current).find(g => g.key === 'amount')!.status, '执行失败');
});

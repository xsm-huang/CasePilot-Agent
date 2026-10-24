import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mergeAnalysisEvent } from '../../../apps/web/src/domain/analysisEvents.ts';
import type { V0AnalysisTask, V0TimelineEvent } from '../../../packages/contracts/src/analysis.ts';

const task = (): V0AnalysisTask => ({
  id: 'analysis-a', caseId: 'case-a', status: 'running', events: [], findings: [], citations: [],
});
const event = (id: number): V0TimelineEvent => ({
  id, type: 'node', at: '2026-10-23T01:00:00.000Z', title: '执行节点', status: 'running',
});

test('a contiguous event produces a new snapshot without mutating the previous one', () => {
  const previous = task();
  const result = mergeAnalysisEvent(previous, event(1));
  assert.equal(result.kind, 'applied');
  if (result.kind !== 'applied') throw new Error('expected an applied event');
  assert.notEqual(result.task, previous);
  assert.equal(result.task.events.length, 1);
  assert.equal(previous.events.length, 0);
});

test('duplicate and missing events do not advance the authoritative snapshot', () => {
  const previous = { ...task(), events: [event(1), event(2)] };
  assert.deepEqual(mergeAnalysisEvent(previous, event(1)), { kind: 'duplicate' });
  assert.deepEqual(mergeAnalysisEvent(previous, event(2)), { kind: 'duplicate' });
  assert.deepEqual(mergeAnalysisEvent(previous, event(4)), { kind: 'gap' });
  assert.equal(previous.events.length, 2);
  assert.equal(mergeAnalysisEvent(previous, event(3)).kind, 'applied');
});

test('review and report events apply validated payloads and terminal status', () => {
  const previous = task();
  const finding = { code: 'MISSING_REPAIR_INVOICE', source: 'rule', severity: 'medium', title: '缺少发票', detail: '待补充' };
  const waiting = mergeAnalysisEvent(previous, {
    ...event(1), type: 'review_required', status: 'waiting_review', data: [finding],
  });
  assert.equal(waiting.kind, 'applied');
  if (waiting.kind !== 'applied') throw new Error('expected waiting task');
  assert.equal(waiting.task.findings.length, 1);
  assert.equal(previous.findings.length, 0);
  const report = { caseId: 'case-a', summary: '摘要', findings: [finding], recommendation: '核查', citations: [] };
  const completed = mergeAnalysisEvent(waiting.task, {
    ...event(2), type: 'report', status: 'completed', data: report,
  });
  assert.equal(completed.kind, 'applied');
  if (completed.kind !== 'applied') throw new Error('expected completed task');
  assert.equal(completed.task.status, 'completed');
  assert.equal(completed.task.report?.summary, '摘要');
  assert.equal(waiting.task.report, undefined);
});

test('malformed review/report payloads fail instead of presenting an unvalidated result', () => {
  const previous = task();
  assert.throws(() => mergeAnalysisEvent(previous, { ...event(1), type: 'review_required', data: [{}] }));
  assert.throws(() => mergeAnalysisEvent(previous, { ...event(1), type: 'report', data: { summary: 'partial' } }));
  assert.equal(previous.events.length, 0);
  assert.equal(previous.report, undefined);
});

import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mergeAnalysisEvent } from '../../../apps/web/src/domain/analysisEvents.ts';
import { workspaceEventSchema, type V1AnalysisTask, type WorkspaceEvent } from '../../../packages/contracts/dist/workspace.js';

// Reducer fixture contains a complete public V1 snapshot, never a legacy write shape.
const task = (): V1AnalysisTask => ({
  schemaVersion: 1, id: 'analysis-a', caseId: 'case-a', conversationId: 'conversation-a', kind: 'initial', question: '核验', status: 'running',
  caseSnapshot: { id: 'case-a', claimant: '测试', productCode: 'AUTO', clauseVersion: '2025-01', claimAmount: 1, policyEffectiveDate: '2026-01-01', accidentDate: '2026-01-02', materials: [] },
  revision: 0, lastEventSeq: 0, userMessageId: 'user-a', assistantMessageId: null,
  context: { caseVersion: 'v1', generationId: 'g1', embeddingProfile: 'e1', messageIds: [], modelProfile: 'm1', promptVersion: 'p1' },
  facts: [], ruleFindings: [], modelFindings: [], citations: [], sections: [], report: null, pendingReview: null, execution: { nodes: [], tools: [], timeline: [] }, error: null,
});
const event = (seq: number): WorkspaceEvent => ({ schemaVersion: 1, analysisId: 'analysis-a', conversationId: 'conversation-a', seq, revision: seq, at: '2026-10-26T01:00:00Z', type: 'analysis.status', data: { status: 'running', revision: seq } });
function apply(previous: V1AnalysisTask, value: WorkspaceEvent) {
  const result = mergeAnalysisEvent(previous, value);
  assert.equal(result.kind, 'applied');
  if (result.kind !== 'applied') throw new Error('Expected applied event');
  return result.task;
}

test('contiguous events produce immutable snapshots; duplicates and gaps preserve the cursor', () => {
  const previous = task(), next = apply(previous, event(1));
  assert.equal(next.lastEventSeq, 1);
  assert.equal(next.execution.timeline.length, 1);
  assert.equal(previous.execution.timeline.length, 0);
  assert.deepEqual(mergeAnalysisEvent(next, event(1)), { kind: 'duplicate' });
  assert.deepEqual(mergeAnalysisEvent(next, event(3)), { kind: 'gap' });
  assert.deepEqual(mergeAnalysisEvent(next, { ...event(2), analysisId: 'another-task' }), { kind: 'gap' });
  assert.deepEqual(mergeAnalysisEvent(next, { ...event(2), conversationId: 'another-conversation' }), { kind: 'gap' });
});

test('review transitions and report commits remain distinct from partial sections', () => {
  const waiting = apply(task(), { ...event(1), type: 'review.required', data: { interruptKey: 'i1', checkpointId: 'cp1', revision: 1, reason: '需核验' } });
  assert.equal(waiting.status, 'waiting_review');
  const resumed = apply(waiting, { ...event(2), type: 'review.accepted', data: { interruptKey: 'i1', decision: 'approve', revision: 2 } });
  assert.equal(resumed.pendingReview, null);
  const section = { sectionKey: 'summary' as const, content: '已保存摘要', factRefs: [], citationRefs: [], committedAt: '2026-10-26T01:00:00Z' };
  const partial = apply(resumed, { ...event(3), type: 'report.section', data: section });
  assert.equal(partial.report, null);
  assert.equal(partial.assistantMessageId, null);
  const completed = apply(partial, { ...event(4), type: 'report.completed', data: { report: { caseId: 'case-a', sections: [section], insufficientEvidence: false, reviewerComment: '核验' }, assistantMessageId: 'assistant-a', revision: 4 } });
  assert.equal(completed.status, 'completed');
  assert.equal(completed.assistantMessageId, 'assistant-a');
  assert.equal(partial.report, null);
});

test('execution completion updates one card and recovery retains committed sections', () => {
  const started = { executionId: 'e1', key: 'model:summary', name: '摘要生成', attempt: 1, status: 'running' as const, summary: '执行中', durationMs: 0 };
  const one = apply(task(), { ...event(1), type: 'node.started', data: started });
  const two = apply(one, { ...event(2), type: 'node.completed', data: { ...started, status: 'completed', durationMs: 125 } });
  assert.equal(two.execution.nodes.length, 1);
  assert.equal(two.execution.nodes[0].durationMs, 125);
  assert.equal(one.execution.nodes[0].status, 'running');
  const tool = apply(two, { ...event(3), type: 'tool.failed', data: { ...started, executionId: 'tool-1', key: 'retrieve', name: '条款检索', status: 'failed', summary: '检索失败' } });
  assert.equal(tool.execution.nodes.length, 1);
  assert.equal(tool.execution.tools.length, 1);
  assert.equal(tool.execution.tools[0].executionId, 'tool-1');
  const failed = apply(tool, { ...event(4), type: 'analysis.recoverable', data: { error: { code: 'MODEL_TIMEOUT', message: '调用超时', requestId: 'r1' }, revision: 4 } });
  assert.equal(failed.status, 'recoverable');
  const retry = apply(failed, { ...event(5), data: { status: 'queued', revision: 5 } });
  assert.equal(retry.error, null);
  assert.equal(retry.execution.nodes.length, 1);
  assert.equal(retry.execution.tools.length, 1);
});

test('transport validation rejects legacy, unknown and malformed event payloads', () => {
  assert.throws(() => workspaceEventSchema.parse({ ...event(1), at: 'yesterday' }));
  const { schemaVersion: _version, ...unversioned } = event(1);
  assert.throws(() => workspaceEventSchema.parse(unversioned));
  assert.throws(() => workspaceEventSchema.parse({ id: 1, type: 'report', data: {} }));
  assert.throws(() => workspaceEventSchema.parse({ ...event(1), type: 'review.required', data: {} }));
  assert.throws(() => workspaceEventSchema.parse({ ...event(1), type: 'report.completed', data: { report: 'incomplete' } }));
  assert.equal(workspaceEventSchema.parse(event(1)).type, 'analysis.status');
});

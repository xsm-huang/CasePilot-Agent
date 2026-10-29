import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mergeAnalysisEvent } from '../../../apps/web/src/domain/analysisEvents.ts';
import { workspaceEventSchema, type AnalysisTask, type WorkspaceEvent } from '../../../packages/contracts/dist/workspace.js';

// Reducer fixture contains a complete public V1 snapshot, never a legacy write shape.
const task = (): AnalysisTask => ({
  reviewState: { reviewModelVersion: 1, checkPlan: [], checks: [], findings: [], findingHistory: [], records: [], businessNodes: [], nodeHistory: [], reviewCycleId: 1 }, finalizationEligibility: { allowed: false, blockers: ['尚未完成'], basisHash: 'a'.repeat(64) }, reviewStatus: 'pending_review', schemaVersion: 2, id: 'analysis-a', caseId: 'case-a', conversationId: 'conversation-a', kind: 'initial', question: '核验', status: 'running',
  caseSnapshot: { snapshotKind: 'closed_claim_review', caseId: 'case-a', caseRevision: 1, preparedAt: '2026-01-01T00:00:00Z', payload: {}, scopeItems: [], knowledgeBindings: [] }, predecessorAnalysisId: null,
  evidenceSupplements: [], reviewSupplementIds: [],
  revision: 0, lastEventSeq: 0, userMessageId: 'user-a', assistantMessageId: null,
  context: { inputVersion: 'v2', knowledgeBindings: [], messageIds: [], modelProfile: 'm1', promptVersion: 'p1' },
  facts: [], ruleFindings: [], modelFindings: [], citations: [], sections: [], report: null, pendingReview: null, execution: { tools: [], timeline: [] }, error: null,
});
const event = (seq: number): WorkspaceEvent => ({ schemaVersion: 2, analysisId: 'analysis-a', conversationId: 'conversation-a', seq, revision: seq, at: '2026-10-26T01:00:00Z', type: 'analysis.status', data: { status: 'running', revision: seq } });
function apply(previous: AnalysisTask, value: WorkspaceEvent) {
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

test('real business-node events stay distinct from tool attempts and failure preserves reports', () => {
  const original = task();
  const node = { nodeRunId: 'amount:1', nodeKey: 'amount' as const, attempt: 1, status: 'not_started' as const, startedAt: null, endedAt: null, durationMs: 0, summary: '', reason: '' };
  original.reviewState.businessNodes = [node];
  const one = apply(original, { ...event(1), type: 'business_node.started', data: { ...node, status: 'running' } });
  const two = apply(one, { ...event(2), type: 'business_node.failed', data: { ...node, status: 'failed', reason: 'MODEL_TIMEOUT' } });
  assert.equal(two.reviewState.businessNodes[0].status, 'failed');
  assert.equal(one.reviewState.businessNodes[0].status, 'running');
  const failed = apply(two, { ...event(3), type: 'analysis.recoverable', data: { error: { code: 'MODEL_TIMEOUT', message: '调用超时', requestId: 'r1' }, revision: 3 } });
  assert.equal(failed.status, 'recoverable');
  assert.equal(failed.reviewState.businessNodes[0].reason, 'MODEL_TIMEOUT');
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

test('saved stage reports and per-finding decisions do not mark the task completed', () => {
  const report = { caseId: 'case-a', kind: 'stage' as const, version: 2, sections: [], insufficientEvidence: true, reviewerComment: null };
  const waiting = { ...task(), status: 'waiting_review' as const };
  const saved = apply(waiting, { ...event(1), type: 'report.saved', data: report });
  assert.equal(saved.status, 'waiting_review');
  assert.equal(saved.report?.version, 2);
  assert.equal(saved.reports?.length, 1);
  assert.equal(waiting.reports, undefined);
  const review = { reviewId: 'r1', findingId: 'payment', nodeKey: 'amount', decision: 'pending' as const, comment: '需核对关联审批', operatorId: '测试001', at: '2026-10-29T00:00:00Z', factRefs: [], citationRefs: [], supplementIds: [], followup: '支付经办补充审批', changeReason: '' };
  const reviewed = apply(saved, { ...event(2), type: 'finding.reviewed', data: { review, report, revision: 2 } });
  assert.equal(reviewed.status, 'waiting_review');
  assert.equal(reviewed.reviewHistory?.[0].comment, '需核对关联审批');
  assert.equal(reviewed.pendingReview, null);
});

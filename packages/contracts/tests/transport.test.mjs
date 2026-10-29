import assert from 'node:assert/strict';
import { test } from 'node:test';
import { analysisTaskSchema, commandAcceptedSchema, reviewPreflightSchema } from '../dist/index.js';

const binding = { documentId: 'terms', documentSha256: 'a'.repeat(64), version: '2020', sectionIds: [], status: 'unavailable', generationId: null, productCode: null, clauseVersion: null, embeddingProfile: null };
const scope = { scopeItemId: 'archive', kind: 'archive_consistency', title: '案卷核验', status: 'executable', entityIds: ['claim'], reason: null, requiredMaterialTypes: [] };
const task = {
  reviewState: { reviewModelVersion: 1, checkPlan: [], checks: [], findings: [], findingHistory: [], records: [], businessNodes: [], nodeHistory: [], reviewCycleId: 1 }, finalizationEligibility: { allowed: false, blockers: ['尚未完成'], basisHash: 'a'.repeat(64) }, reviewStatus: 'pending_review', schemaVersion: 2, id: 'a', caseId: 'C01', conversationId: 'c', kind: 'initial', question: '核验', status: 'queued',
  caseSnapshot: { snapshotKind: 'closed_claim_review', caseId: 'C01', caseRevision: 1, preparedAt: '2026-10-01T00:00:00Z', payload: {}, scopeItems: [scope], knowledgeBindings: [binding] },
  predecessorAnalysisId: null, evidenceSupplements: [], reviewSupplementIds: [], revision: 0, lastEventSeq: 0, userMessageId: 'm', assistantMessageId: null,
  context: { inputVersion: 'b'.repeat(64), knowledgeBindings: [binding], messageIds: [], modelProfile: 'model', promptVersion: 'prompt' },
  facts: [], ruleFindings: [], modelFindings: [], citations: [], sections: [], report: null, pendingReview: null,
  execution: { tools: [], timeline: [] }, error: null,
};

test('closed-claim task contract accepts only the current fixed-input shape', () => {
  assert.deepEqual(analysisTaskSchema.parse(task), task);
  assert.throws(() => analysisTaskSchema.parse({ ...task, schemaVersion: 1 }));
  assert.throws(() => analysisTaskSchema.parse({ ...task, caseSnapshot: { id: 'legacy' } }));
});

test('preflight separates partial execution from blocking', () => {
  const value = { caseId: 'C03', expectedInputVersion: 'b'.repeat(64), status: 'partial', reviewObjects: { targetClaimIds: ['claim'], relatedClaimIds: [], vehicleIds: [], lossIds: [], scopeLimitations: [] }, applicablePolicies: [], scopeItems: [scope], knowledgeBindings: [binding], materialSummary: { available: 2, notObtained: 1, unavailable: 0 }, injuryStatus: 'unknown', injuredPersonIds: [], blockingReasons: [] };
  assert.deepEqual(reviewPreflightSchema.parse(value), value);
  assert.throws(() => reviewPreflightSchema.parse({ ...value, status: 'unknown' }));
});

test('command acknowledgement requires literal true and task identity', () => {
  assert.deepEqual(commandAcceptedSchema.parse({ accepted: true, taskId: 'a', revision: 1 }), { accepted: true, taskId: 'a', revision: 1 });
  assert.throws(() => commandAcceptedSchema.parse({ accepted: false, taskId: 'a', revision: 1 }));
});

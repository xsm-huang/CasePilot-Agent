import { analysisTaskSchema, conversationSchema, conversationSummarySchema, commandAcceptedSchema, citationContextSchema, evidenceSupplementSchema } from '@casepilot/contracts';
import { request } from './http';
import type { CreateAnalysis, ReviewRequest, FindingReviewRequest, ReviewRecordRequest, ManualFindingRequest } from '@casepilot/contracts';
const enc = encodeURIComponent;
export const workbenchApi = {
  history: (signal: AbortSignal) => request('/analyses', analysisTaskSchema.array(), { signal }),
  task: (id: string, signal: AbortSignal) => request(`/analyses/${enc(id)}`, analysisTaskSchema, { signal }),
  conversations: (caseId: string, signal: AbortSignal) => request(`/conversations?caseId=${enc(caseId)}`, conversationSummarySchema.array(), { signal }),
  conversation: (id: string, signal: AbortSignal, before?: string) => request(`/conversations/${enc(id)}${before ? `?before=${enc(before)}` : ''}`, conversationSchema, { signal }),
  createConversation: (caseId: string, signal: AbortSignal) => request(`/cases/${enc(caseId)}/conversations`, conversationSummarySchema, { signal, body: { title: '案件分析' } }),
  start: (body: CreateAnalysis, key: string, signal: AbortSignal) => request('/analyses', analysisTaskSchema, { signal, body, headers: { 'Idempotency-Key': key } }),
  review: (id: string, body: ReviewRequest, key: string, signal: AbortSignal) => request(`/analyses/${enc(id)}/review`, commandAcceptedSchema, { signal, body, headers: { 'Idempotency-Key': key } }),
  reviewFinding: (id: string, findingId: string, body: FindingReviewRequest, key: string, signal: AbortSignal) => request(`/analyses/${enc(id)}/findings/${enc(findingId)}/review`, commandAcceptedSchema, { signal, body, headers: { 'Idempotency-Key': key } }),
  record: (id: string, action: string, body: ReviewRecordRequest, key: string, signal: AbortSignal) => request(`/analyses/${enc(id)}/${action}`, commandAcceptedSchema, { signal, body, headers: { 'Idempotency-Key': key } }),
  manualFinding: (id: string, body: ManualFindingRequest, key: string, signal: AbortSignal) => request(`/analyses/${enc(id)}/findings`, commandAcceptedSchema, { signal, body, headers: { 'Idempotency-Key': key } }),
  recover: (id: string, revision: number, key: string, signal: AbortSignal) => request(`/analyses/${enc(id)}/recover`, commandAcceptedSchema, { signal, body: { expectedRevision: revision }, headers: { 'Idempotency-Key': key } }),
  citation: (id: string, citationId: string, signal: AbortSignal) => request(`/analyses/${enc(id)}/citations/${enc(citationId)}/context`, citationContextSchema, { signal }),
  supplement: (id: string, body: FormData, key: string, signal: AbortSignal) => request(`/analyses/${enc(id)}/supplements`, evidenceSupplementSchema, { signal, body, headers: { 'Idempotency-Key': key } }),
};

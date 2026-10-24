import { v0AnalysisTaskSchema, v0ClaimCaseSchema, v0ReviewAcceptedSchema } from '@casepilot/contracts';
import { request } from './http';

export const workbenchApi = {
  cases: (signal: AbortSignal) => request('/cases', v0ClaimCaseSchema.array(), { signal }),
  history: (signal: AbortSignal) => request('/analyses', v0AnalysisTaskSchema.array(), { signal }),
  task: (id: string, signal: AbortSignal) => request(`/analyses/${encodeURIComponent(id)}`, v0AnalysisTaskSchema, { signal }),
  start: (caseId: string, signal: AbortSignal) => request('/analyses', v0AnalysisTaskSchema, { signal, body: { caseId } }),
  review: (id: string, decision: 'approve' | 'reject', comment: string, signal: AbortSignal) => request(
    `/analyses/${encodeURIComponent(id)}/review`, v0ReviewAcceptedSchema, { signal, body: { decision, comment } }
  )
};

import { v0AnalysisTaskSchema, v0ClaimCaseSchema } from '@casepilot/contracts';
import { request } from './http';

const reviewAccepted = {
  parse(value: unknown): void {
    if (typeof value !== 'object' || value === null || !('accepted' in value) || value.accepted !== true) {
      throw new Error('审核响应格式不正确，请重新读取任务状态。');
    }
  }
};

export const workbenchApi = {
  cases: (signal: AbortSignal) => request('/cases', v0ClaimCaseSchema.array(), { signal }),
  history: (signal: AbortSignal) => request('/analyses', v0AnalysisTaskSchema.array(), { signal }),
  task: (id: string, signal: AbortSignal) => request(`/analyses/${encodeURIComponent(id)}`, v0AnalysisTaskSchema, { signal }),
  start: (caseId: string, signal: AbortSignal) => request('/analyses', v0AnalysisTaskSchema, { signal, body: { caseId } }),
  review: (id: string, decision: 'approve' | 'reject', comment: string, signal: AbortSignal) => request(
    `/analyses/${encodeURIComponent(id)}/review`, reviewAccepted, { signal, body: { decision, comment } }
  )
};

import { reviewCaseDetailSchema, reviewCaseListResponseSchema, reviewPreflightSchema } from '@casepilot/contracts';
import { request } from './http';

export interface ReviewCaseFilters {
  queryType: '' | 'claim_number' | 'report_number' | 'plate_number';
  query: string;
  closedFrom: string;
  closedTo: string;
  injuryStatus: string;
  reviewStatus: string;
}

const enc = encodeURIComponent;

export const reviewCasesApi = {
  list(filters: ReviewCaseFilters, signal: AbortSignal) {
    const params = new URLSearchParams();
    if (filters.query.trim()) {
      params.set('queryType', filters.queryType);
      params.set('query', filters.query.trim());
    }
    if (filters.closedFrom) params.set('closedFrom', filters.closedFrom);
    if (filters.closedTo) params.set('closedTo', filters.closedTo);
    if (filters.injuryStatus) params.set('injuryStatus', filters.injuryStatus);
    if (filters.reviewStatus) params.set('reviewStatus', filters.reviewStatus);
    const suffix = params.size ? `?${params.toString()}` : '';
    return request(`/review-cases${suffix}`, reviewCaseListResponseSchema, { signal });
  },
  detail(id: string, signal: AbortSignal) {
    return request(`/review-cases/${enc(id)}`, reviewCaseDetailSchema, { signal });
  },
  preflight(id: string, signal: AbortSignal) {
    return request(`/review-cases/${enc(id)}/review-preflight`, reviewPreflightSchema, { signal });
  },
};

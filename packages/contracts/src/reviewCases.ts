import type { ReviewCaseDetail, ReviewCaseListItem, ReviewCaseListResponse, ReviewPreflight } from './generated/types.js';
import { transportValidator } from './transport.js';

export type {
  ReviewCaseDetail, ReviewCaseListItem, ReviewCaseListResponse, ReviewPreflight, ReviewMoney, ReviewEvidenceSource,
} from './generated/types.js';

export const reviewCaseListResponseSchema = transportValidator<ReviewCaseListResponse>('ReviewCaseListResponse');
export const reviewCaseDetailSchema = transportValidator<ReviewCaseDetail>('ReviewCaseDetail');
export const reviewCaseListItemSchema = transportValidator<ReviewCaseListItem>('ReviewCaseListItem');
export const reviewPreflightSchema = transportValidator<ReviewPreflight>('ReviewPreflight');

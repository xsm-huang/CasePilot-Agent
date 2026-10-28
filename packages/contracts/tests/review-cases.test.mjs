import assert from 'node:assert/strict';
import { test } from 'node:test';
import { reviewCaseListResponseSchema } from '../dist/index.js';

const response = {
  dataStatus: 'ready',
  items: [{
    id: 'C03', revision: 1,
    targetClaims: [{ claimId: 'CLM-C03-COM-TP', claimNumber: 'DEMO-CLM-C03-COM-TP', reportNumber: 'DEMO-RPT-C03', scopeRole: 'target', closureType: 'paid_closed', closedAt: '2026-06-15T16:30:00+08:00', originalPaymentStatus: 'settled' }],
    relatedClaims: [], vehicles: [{ vehicleId: 'VEH-C03-A', role: 'insured', plateNumber: '演示-C03A' }], accidentAt: '2026-06-08T09:10:00+08:00',
    originalApprovedAmount: { status: 'known', amountFen: 800000, currency: 'CNY', reason: null },
    effectivePaidAmount: { status: 'known', amountFen: 900000, currency: 'CNY', reason: null },
    injuryStatus: 'no_injury_reported', latestReviewStatus: 'not_started',
  }],
};

test('review-case list contract keeps approved and paid amounts separate', () => {
  assert.equal(reviewCaseListResponseSchema.parse(response).items[0].effectivePaidAmount.amountFen, 900000);
  assert.throws(() => reviewCaseListResponseSchema.parse({ ...response, items: [{ ...response.items[0], originalApprovedAmount: undefined }] }), /契约/);
});

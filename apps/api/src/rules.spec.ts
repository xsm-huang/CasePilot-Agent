import { describe, expect, it } from 'vitest';
import { cases } from './fixtures.js';
import { evaluateClaimRules } from './rules.js';

describe('evaluateClaimRules', () => {
  it('finds missing invoice and pre-policy accident deterministically', () => {
    expect(evaluateClaimRules(cases[0]).map((item) => item.code)).toEqual([
      'MISSING_REPAIR_INVOICE', 'ACCIDENT_BEFORE_POLICY'
    ]);
  });

  it('allows a complete and date-valid case through', () => {
    expect(evaluateClaimRules(cases[1])).toEqual([]);
  });
});

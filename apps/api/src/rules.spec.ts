import { describe, expect, it } from 'vitest';
import { cases } from './fixtures.js';
import { evaluateClaimRules } from './rules.js';

describe('evaluateClaimRules', () => {
  it('finds missing invoice and pre-policy accident deterministically', () => {
    const findings = evaluateClaimRules(cases[0]);
    expect(findings.map((item) => item.code)).toEqual([
      'MISSING_REPAIR_INVOICE', 'ACCIDENT_BEFORE_POLICY'
    ]);
    expect(findings.every((item) => item.source === 'rule')).toBe(true);
  });

  it('allows a complete and date-valid case through', () => {
    expect(evaluateClaimRules(cases[1])).toEqual([]);
  });
});

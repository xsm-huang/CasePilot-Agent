import { describe, expect, it } from 'vitest';
import { ClauseRepository } from './clause.repository.js';

describe('ClauseRepository', () => {
  it('filters by product/version and returns traceable citations', () => {
    const result = new ClauseRepository().search('AUTO-COMPREHENSIVE', '2025-01', [
      { code: 'MISSING_REPAIR_INVOICE', severity: 'medium', title: '维修发票缺失', detail: '材料缺失' }
    ]);
    expect(result[0].id).toBe('AUTO-2025-01-18');
    expect(result.some((item) => item.id.includes('2024'))).toBe(false);
  });
});

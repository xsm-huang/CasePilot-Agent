import assert from 'node:assert/strict';
import { test } from 'node:test';
import { formatMoney, label } from '../../../apps/web/src/domain/reviewCases.ts';

test('review-case presentation keeps amount meanings and injury declaration explicit', () => {
  assert.equal(formatMoney({ status: 'known', amountFen: 800000, currency: 'CNY', reason: null }), '¥8,000.00');
  assert.equal(formatMoney({ status: 'unknown', amountFen: null, currency: 'CNY', reason: '未取得计算书' }), '未知（未取得计算书）');
  assert.equal(label('no_injury_reported'), '原档案记录未报人伤');
  assert.equal(label('paid_closed'), '赔付结案');
});

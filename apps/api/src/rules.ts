import type { ClaimCase, Finding } from './domain.js';

export function evaluateClaimRules(claim: ClaimCase): Finding[] {
  const findings: Finding[] = [];
  const materialTypes = new Set(claim.materials.map((item) => item.type));

  if (!materialTypes.has('repair_invoice')) {
    findings.push({ code: 'MISSING_REPAIR_INVOICE', source: 'rule', severity: 'medium', title: '维修发票缺失', detail: '当前材料目录中未发现维修发票，无法核验实际修复费用。' });
  }
  if (claim.accidentDate < claim.policyEffectiveDate) {
    findings.push({ code: 'ACCIDENT_BEFORE_POLICY', source: 'rule', severity: 'high', title: '事故早于保单生效', detail: `事故日期 ${claim.accidentDate} 早于保单生效日期 ${claim.policyEffectiveDate}。` });
  }
  const declaredDates = claim.materials
    .map((item) => item.fields.accidentDate)
    .filter((value): value is string => typeof value === 'string');
  if (new Set(declaredDates).size > 1) {
    findings.push({ code: 'ACCIDENT_DATE_CONFLICT', source: 'rule', severity: 'high', title: '跨材料事故日期冲突', detail: `材料中出现多个事故日期：${[...new Set(declaredDates)].join('、')}。` });
  }
  return findings;
}

import type { ClaimCase, Clause } from './domain.js';

export const cases: ClaimCase[] = [
  {
    id: 'CASE-2026-001', claimant: '张某', productCode: 'AUTO-COMPREHENSIVE', clauseVersion: '2025-01',
    policyEffectiveDate: '2026-08-10', accidentDate: '2026-08-08', claimAmount: 28600,
    materials: [
      { type: 'claim_form', name: '索赔申请书.pdf', fields: { accidentDate: '2026-08-08', claimAmount: 28600 } },
      { type: 'accident_certificate', name: '事故认定书.pdf', fields: { accidentDate: '2026-08-08', liability: '被保险人全责' } },
      { type: 'damage_assessment', name: '定损单.pdf', fields: { assessedAmount: 27500 } }
    ]
  },
  {
    id: 'CASE-2026-002', claimant: '李某', productCode: 'AUTO-COMPREHENSIVE', clauseVersion: '2025-01',
    policyEffectiveDate: '2026-06-01', accidentDate: '2026-09-12', claimAmount: 8200,
    materials: [
      { type: 'claim_form', name: '索赔申请书.pdf', fields: { accidentDate: '2026-09-12', claimAmount: 8200 } },
      { type: 'accident_certificate', name: '事故认定书.pdf', fields: { accidentDate: '2026-09-12', liability: '对方全责' } },
      { type: 'damage_assessment', name: '定损单.pdf', fields: { assessedAmount: 8100 } },
      { type: 'repair_invoice', name: '维修发票.pdf', fields: { invoiceAmount: 8100 } }
    ]
  }
];

export const clauses: Clause[] = [
  { id: 'AUTO-2025-01-04', productCode: 'AUTO-COMPREHENSIVE', version: '2025-01', title: '第四条 保险期间', content: '保险人仅对保险期间内发生的保险事故承担保险责任。', keywords: ['保险期间', '生效日期', '事故日期', '日期冲突'] },
  { id: 'AUTO-2025-01-18', productCode: 'AUTO-COMPREHENSIVE', version: '2025-01', title: '第十八条 索赔材料', content: '被保险人请求赔偿时，应提供索赔申请书、事故证明、损失清单及维修发票等能够确认事故性质、原因和损失程度的材料。', keywords: ['材料缺失', '维修发票', '索赔材料'] },
  { id: 'AUTO-2025-01-22', productCode: 'AUTO-COMPREHENSIVE', version: '2025-01', title: '第二十二条 损失核定', content: '保险人依据事故责任、实际修复费用及保险合同约定核定赔偿金额。', keywords: ['金额', '定损', '维修费用'] },
  { id: 'AUTO-2024-01-18', productCode: 'AUTO-COMPREHENSIVE', version: '2024-01', title: '旧版第十八条', content: '此条款不应被 2025-01 版本案件检索到。', keywords: ['材料缺失'] }
];

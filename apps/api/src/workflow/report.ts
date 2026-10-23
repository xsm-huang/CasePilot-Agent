import type { AnalysisReport } from '../domain.js';
import type { AnalysisWorkflowState } from './state.js';

/** V0 deterministic report retained during G1; real model sections arrive in G3/G4. */
export function buildPrototypeReport(state: AnalysisWorkflowState): AnalysisReport {
  return {
    caseId: state.caseId,
    summary: `${state.claim.claimant}就车辆损失申请理赔 ${state.claim.claimAmount.toLocaleString('zh-CN')} 元，共提交 ${state.claim.materials.length} 份材料。`,
    findings: state.findings,
    recommendation: state.findings.some(item => item.code === 'ACCIDENT_BEFORE_POLICY')
      ? '建议暂缓赔付，优先核验事故发生时间与保险责任起期。'
      : state.findings.length ? '建议补齐材料后复核赔付金额。' : '未发现规则层面的显著疑点，可进入常规核赔。',
    citations: state.citations,
    reviewerComment: state.review?.comment
  };
}

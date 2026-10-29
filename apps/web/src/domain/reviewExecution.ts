import type { AnalysisTask } from '@casepilot/contracts';
export const nodeNames = { archive: '档案整理与范围识别', coverage: '保单与承保险种核验', consistency: '材料一致性核对', clauses: '条款检索与依据核对', amount: '金额与支付核对', report: '发现与报告汇总' };
export const nodeStatuses = { not_started: '未开始', running: '执行中', completed: '已完成', failed: '执行失败', unable: '无法执行', not_applicable: '不适用' };
export const checkLabels = { passed: '检查通过', issue: '业务疑点', limited: '资料或依据受限', not_applicable: '不适用', out_of_scope: '范围外提示' };
export const decisionLabels = { confirmed: '确认问题', excluded: '排除疑点', pending: '待补充核实', referred: '转专业复核' };
export const sectionNames = { summary: '审查结论与范围', coverage: '检查覆盖', findings: '审查发现', limitations: '范围与判断限制', reviews: '人工复核记录', recommendations: '后续建议及人工记录' };
export const recordLabels = { evidence_view: '查看依据', human_completion: '人工补做检查', scope_adjustment: '调整审查范围', professional: '专业复核', followup: '后续办理', business_record: '补充业务记录', reopen: '重新打开复核' };
export function unresolved(task: AnalysisTask) { return task.finalizationEligibility.blockers; }
export function executionGroups(task: AnalysisTask) {
  return task.reviewState.businessNodes.map(node => {
    const key = node.nodeKey;
    const entries = task.execution.tools.filter(e => e.nodeKey === key).map(entry => ({ ...entry, startedAt: task.execution.timeline.find(e => e.type === 'tool.started' && e.data.executionId === entry.executionId)?.at }));
    const checks = task.reviewState.checks.filter(c => c.nodeKey === key);
    const findings = task.reviewState.findings.filter(f => f.nodeKey === key && f.active);
    const reviews = (task.reviewHistory ?? []).filter(r => r.nodeKey === key);
    const records = task.reviewState.records.filter(r => r.nodeKey === key && r.kind !== 'evidence_view');
    const events = task.execution.timeline.filter(e => e.type === 'finding.reviewed' && e.data.review.nodeKey === key
      || (e.type === 'review.accepted' || e.type === 'review.required' || e.type === 'report.saved' || e.type === 'report.completed') && key === 'report'
      || e.type === 'evidence.supplemented' && e.data.supplement.nodeKey === key);
    const positiveText = checks.filter(c => ['passed', 'not_applicable'].includes(c.status)).map(c => `${checkLabels[c.status]} · ${c.title}：${c.detail}`).join('\n');
    return { key, name: nodeNames[key], node, status: nodeStatuses[node.status], entries, checks, findings, reviews, events, records, positiveText };
  });
}

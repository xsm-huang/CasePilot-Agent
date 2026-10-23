import type { V0AnalysisStatus, V0Finding } from '@casepilot/contracts';
export const statusText: Record<V0AnalysisStatus, string> = {
  running: '分析中', waiting_review: '等待审核', completed: '已完成', rejected: '已驳回', failed: '执行失败'
};
export const findingSourceText: Record<V0Finding['source'], string> = {
  rule: '规则命中',
  ai: 'AI 分析'
};
export function isTerminal(status: V0AnalysisStatus) {
  return status === 'completed' || status === 'rejected' || status === 'failed';
}

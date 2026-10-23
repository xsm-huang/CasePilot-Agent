import type { V0AnalysisStatus } from '@casepilot/contracts';
export const statusText: Record<V0AnalysisStatus, string> = {
  running: '分析中', waiting_review: '等待审核', completed: '已完成', rejected: '已驳回', failed: '执行失败'
};
export function isTerminal(status: V0AnalysisStatus) {
  return status === 'completed' || status === 'rejected' || status === 'failed';
}

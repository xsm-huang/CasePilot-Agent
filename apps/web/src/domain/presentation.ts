import type { AnalysisTask } from '@casepilot/contracts';
export const statusText: Record<AnalysisTask['status'], string> = {
  queued: '排队中', resuming: '恢复中', recoverable: '等待恢复', running: '分析中', waiting_review: '等待审核', completed: '已完成', rejected: '已驳回', failed: '执行失败'
};
export function isTerminal(status: string) {
  return ['completed', 'rejected', 'failed', 'recoverable', 'waiting_review'].includes(status);
}

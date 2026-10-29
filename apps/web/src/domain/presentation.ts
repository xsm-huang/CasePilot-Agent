import type { AnalysisTask } from '@casepilot/contracts';
export const statusText: Record<AnalysisTask['status'], string> = {
  queued: '排队中', resuming: '正在保存报告', recoverable: '等待恢复', running: '审查执行中', waiting_review: '待人工复核', completed: '执行已完成', rejected: '本次审查已终止', failed: '执行失败'
};
export function isTerminal(status: string) {
  return ['completed', 'rejected', 'failed', 'recoverable', 'waiting_review'].includes(status);
}
export function reviewStatus(task: AnalysisTask) {
  if (task.status === 'completed') return task.report?.kind === 'final' ? '车损审查完成' : '执行结束，业务待核实';
  if (task.status === 'waiting_review' && task.reviewStatus === 'pending_verification') return '待核实';
  if (task.status === 'waiting_review' && task.reviewStatus === 'reviewing') return '复核中';
  return statusText[task.status];
}

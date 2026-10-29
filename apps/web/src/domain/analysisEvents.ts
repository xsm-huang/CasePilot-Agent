import type { AnalysisTask, WorkspaceEvent } from '@casepilot/contracts';
export type EventResult = { kind: 'duplicate' } | { kind: 'gap' } | { kind: 'applied'; task: AnalysisTask };
function unreachable(value: never): never { throw new Error(`未处理的工作台事件：${String(value)}`); }
/** Only apply events belonging to this exact task and a contiguous persisted cursor. */
export function mergeAnalysisEvent(task: AnalysisTask, event: WorkspaceEvent): EventResult {
  if (event.analysisId !== task.id || event.conversationId !== task.conversationId) return { kind: 'gap' };
  if (event.seq <= task.lastEventSeq) return { kind: 'duplicate' };
  if (event.seq !== task.lastEventSeq + 1 || event.revision <= task.revision) return { kind: 'gap' };
  const eventType = event.type;
  const next: AnalysisTask = { ...task, lastEventSeq: event.seq, revision: event.revision,
    execution: { ...task.execution, timeline: [...task.execution.timeline, event] } };
  switch (eventType) {
    case 'analysis.status':
      next.status = event.data.status;
      if (next.status === 'queued' || next.status === 'running') next.error = null;
      return { kind: 'applied', task: next };
    case 'analysis.ready':
      Object.assign(next, { facts: event.data.facts, ruleFindings: event.data.ruleFindings, modelFindings: event.data.modelFindings, citations: event.data.citations, checks: event.data.checks ?? [] });
      return { kind: 'applied', task: next };
    case 'review.required':
      next.status = 'waiting_review'; next.pendingReview = event.data;
      return { kind: 'applied', task: next };
    case 'review.accepted':
      next.status = 'resuming'; next.pendingReview = null;
      return { kind: 'applied', task: next };
    case 'report.saved':
      next.report = event.data; next.sections = event.data.sections;
      next.reports = [...(task.reports ?? []).filter(r => r.version !== event.data.version), event.data];
      return { kind: 'applied', task: next };
    case 'finding.reviewed':
      next.reviewHistory = [...(task.reviewHistory ?? []), event.data.review];
      next.report = event.data.report; next.sections = event.data.report.sections;
      return { kind: 'applied', task: next };
    case 'report.section':
      next.sections = [...task.sections.filter(s => s.sectionKey !== event.data.sectionKey), event.data];
      return { kind: 'applied', task: next };
    case 'report.completed':
      next.status = 'completed'; next.report = event.data.report; next.assistantMessageId = event.data.assistantMessageId;
      return { kind: 'applied', task: next };
    case 'analysis.failed':
    case 'analysis.recoverable':
      next.status = event.type === 'analysis.failed' ? 'failed' : 'recoverable'; next.error = event.data.error;
      return { kind: 'applied', task: next };
    case 'analysis.rejected':
      next.status = 'rejected'; next.pendingReview = null;
      return { kind: 'applied', task: next };
    case 'evidence.supplemented':
      next.evidenceSupplements = [...task.evidenceSupplements, event.data.supplement];
      return { kind: 'applied', task: next };
    case 'tool.started':
    case 'tool.completed':
    case 'tool.failed':
      next.execution.tools = [...task.execution.tools.filter(x => x.executionId !== event.data.executionId), event.data];
      return { kind: 'applied', task: next };
    case 'business_node.started':
    case 'business_node.completed':
    case 'business_node.failed':
    case 'business_node.unable':
    case 'business_node.not_applicable':
      next.reviewState = { ...task.reviewState, businessNodes: task.reviewState.businessNodes.map(n => n.nodeKey === event.data.nodeKey ? event.data : n) };
      return { kind: 'applied', task: next };
    case 'review.updated':
      next.reviewState = event.data; next.checks = event.data.checks;
      return { kind: 'applied', task: next };
  }
  return unreachable(eventType);
}

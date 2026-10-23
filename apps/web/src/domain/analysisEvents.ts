import { v0AnalysisReportSchema, v0FindingSchema, type V0AnalysisTask, type V0TimelineEvent } from '@casepilot/contracts';

export type EventResult = { kind: 'duplicate' } | { kind: 'gap' } | { kind: 'applied'; task: V0AnalysisTask };

/** Applies one contiguous event without mutating the previous snapshot. */
export function mergeAnalysisEvent(task: V0AnalysisTask, event: V0TimelineEvent): EventResult {
  const cursor = task.events.at(-1)?.id ?? 0;
  if (event.id <= cursor) return { kind: 'duplicate' };
  if (event.id !== cursor + 1) return { kind: 'gap' };
  const updated = { ...task, status: event.status, events: [...task.events, event] };
  if (event.type === 'review_required') updated.findings = v0FindingSchema.array().parse(event.data);
  if (event.type === 'report') updated.report = v0AnalysisReportSchema.parse(event.data);
  return { kind: 'applied', task: updated };
}

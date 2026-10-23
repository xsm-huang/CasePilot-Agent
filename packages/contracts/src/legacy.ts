import { z } from 'zod';

// V0 transport boundary. Kept explicit while V1 resources are implemented stage by stage.
export const v0MaterialSchema = z.object({
  type: z.string(), name: z.string(),
  fields: z.record(z.string(), z.union([z.string(), z.number()]))
});
export type V0Material = z.infer<typeof v0MaterialSchema>;

export const v0ClaimCaseSchema = z.object({
  id: z.string(), claimant: z.string(), productCode: z.string(), clauseVersion: z.string(),
  policyEffectiveDate: z.string(), accidentDate: z.string(), claimAmount: z.number(),
  materials: z.array(v0MaterialSchema)
});
export type V0ClaimCase = z.infer<typeof v0ClaimCaseSchema>;

export const v0FindingSchema = z.object({
  code: z.string(), severity: z.enum(['low', 'medium', 'high']), title: z.string(), detail: z.string()
});
export type V0Finding = z.infer<typeof v0FindingSchema>;

export const v0ClauseSchema = z.object({
  id: z.string(), productCode: z.string(), version: z.string(), title: z.string(),
  content: z.string(), keywords: z.array(z.string())
});
export type V0Clause = z.infer<typeof v0ClauseSchema>;

export const v0ClauseCitationSchema = v0ClauseSchema.pick({ id: true, title: true, content: true })
  .extend({ score: z.number() });
export type V0ClauseCitation = z.infer<typeof v0ClauseCitationSchema>;

export const v0AnalysisReportSchema = z.object({
  caseId: z.string(), summary: z.string(), findings: z.array(v0FindingSchema),
  recommendation: z.string(), citations: z.array(v0ClauseCitationSchema), reviewerComment: z.string().optional()
});
export type V0AnalysisReport = z.infer<typeof v0AnalysisReportSchema>;

export const v0AnalysisStatusSchema = z.enum(['running', 'waiting_review', 'completed', 'rejected', 'failed']);
export type V0AnalysisStatus = z.infer<typeof v0AnalysisStatusSchema>;

export const v0TimelineEventSchema = z.object({
  id: z.number().int().positive(), type: z.enum(['status', 'node', 'tool', 'review_required', 'report', 'error']),
  at: z.iso.datetime(), title: z.string(), detail: z.string().optional(),
  data: z.unknown().optional(), status: v0AnalysisStatusSchema
});
export type V0TimelineEvent = z.infer<typeof v0TimelineEventSchema>;

export const v0AnalysisTaskSchema = z.object({
  id: z.string(), caseId: z.string(), status: v0AnalysisStatusSchema,
  events: z.array(v0TimelineEventSchema), findings: z.array(v0FindingSchema),
  citations: z.array(v0ClauseCitationSchema), report: v0AnalysisReportSchema.optional(),
  review: z.object({ decision: z.enum(['approve', 'reject']), comment: z.string() }).optional()
});
export type V0AnalysisTask = z.infer<typeof v0AnalysisTaskSchema>;

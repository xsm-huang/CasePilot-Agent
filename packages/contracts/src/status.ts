import { z } from 'zod';

export const analysisStatusSchema = z.enum([
  'queued', 'running', 'waiting_review', 'resuming', 'recoverable',
  'completed', 'rejected', 'failed'
]);
export type AnalysisStatus = z.infer<typeof analysisStatusSchema>;

export const knowledgeStatusSchema = z.enum([
  'queued', 'parsing', 'chunking', 'embedding', 'ready', 'failed'
]);
export type KnowledgeStatus = z.infer<typeof knowledgeStatusSchema>;

export const sectionKeySchema = z.enum(['summary', 'findings', 'recommendations']);
export type SectionKey = z.infer<typeof sectionKeySchema>;

export const activeAnalysisStatuses = [
  'queued', 'running', 'waiting_review', 'resuming', 'recoverable'
] as const satisfies readonly AnalysisStatus[];

export const terminalAnalysisStatuses = [
  'completed', 'rejected', 'failed'
] as const satisfies readonly AnalysisStatus[];

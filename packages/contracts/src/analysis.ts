// Legacy report reads and shared illustrative case models. V1 writes use workspace.ts.
// Shapes and validation come exclusively from exported Python response models.
import type {
  V0AnalysisTask, V0AnalysisReport, V0ClaimCase, V0Material, V0Finding,
  V0Clause, V0ClauseCitation, V0TimelineEvent, V0ReviewAccepted,
} from './generated/types.js';
import { transportValidator } from './transport.js';

export type {
  V0AnalysisTask, V0AnalysisReport, V0ClaimCase, V0Material, V0Finding,
  V0Clause, V0ClauseCitation, V0TimelineEvent, V0ReviewAccepted,
} from './generated/types.js';
export type V0AnalysisStatus = V0AnalysisTask['status'];

export const v0MaterialSchema = transportValidator<V0Material>('V0Material');
export const v0ClaimCaseSchema = transportValidator<V0ClaimCase>('V0ClaimCase');
export const v0FindingSchema = transportValidator<V0Finding>('V0Finding');
export const v0ClauseSchema = transportValidator<V0Clause>('V0Clause');
export const v0ClauseCitationSchema = transportValidator<V0ClauseCitation>('V0ClauseCitation');
export const v0AnalysisReportSchema = transportValidator<V0AnalysisReport>('V0AnalysisReport');
export const v0AnalysisTaskSchema = transportValidator<V0AnalysisTask>('V0AnalysisTask');
export const v0TimelineEventSchema = transportValidator<V0TimelineEvent>('V0TimelineEvent');
export const v0ReviewAcceptedSchema = transportValidator<V0ReviewAccepted>('V0ReviewAccepted');

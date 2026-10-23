import { Annotation } from '@langchain/langgraph';
import type { AnalysisReport, ClaimCase, ClauseCitation, Finding } from '../domain.js';

export type Review = { decision: 'approve' | 'reject'; comment: string };

export const WorkflowState = Annotation.Root({
  taskId: Annotation<string>(),
  caseId: Annotation<string>(),
  claim: Annotation<ClaimCase>(),
  findings: Annotation<Finding[]>(),
  citations: Annotation<ClauseCitation[]>(),
  review: Annotation<Review>(),
  report: Annotation<AnalysisReport>()
});

export type AnalysisWorkflowState = typeof WorkflowState.State;

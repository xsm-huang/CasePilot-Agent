import { END, MemorySaver, START, StateGraph } from '@langchain/langgraph';
import type { AnalysisStore } from '../analysis.store.js';
import type { ClauseRepository } from '../clause.repository.js';
import { createPrototypeNodes } from './nodes.js';
import { WorkflowState } from './state.js';

/** G1 keeps the V0 persistence boundary. G4 will wire the durable application state. */
export function createPrototypeGraph(store: AnalysisStore, clauses: ClauseRepository) {
  const nodes = createPrototypeNodes(store, clauses);
  return new StateGraph(WorkflowState)
    .addNode('query_case', nodes.queryCase)
    .addNode('validate_materials', nodes.validateMaterials)
    .addNode('retrieve_clauses', nodes.retrieveClauses)
    .addNode('human_review', nodes.humanReview)
    .addNode('generate_report', nodes.generateReport)
    .addEdge(START, 'query_case')
    .addEdge('query_case', 'validate_materials')
    .addEdge('validate_materials', 'retrieve_clauses')
    .addConditionalEdges('retrieve_clauses', state => state.findings.length > 0 ? 'human_review' : 'generate_report')
    .addEdge('human_review', 'generate_report')
    .addEdge('generate_report', END)
    .compile({ checkpointer: new MemorySaver() });
}

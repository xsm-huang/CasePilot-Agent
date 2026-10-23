import { interrupt } from '@langchain/langgraph';
import type { AnalysisStore } from '../analysis.store.js';
import type { ClauseRepository } from '../clause.repository.js';
import { evaluateClaimRules } from '../rules.js';
import { buildPrototypeReport } from './report.js';
import type { AnalysisWorkflowState, Review } from './state.js';

export function createPrototypeNodes(store: AnalysisStore, clauses: ClauseRepository) {
  return {
    queryCase: async (state: AnalysisWorkflowState) => {
      store.emit(state.taskId, 'node', '案件查询完成', `读取案件 ${state.claim.id} 及 ${state.claim.materials.length} 份材料`);
      store.emit(state.taskId, 'tool', 'Tool · queryCase', '获取保单、报案和材料结构化字段');
      return {};
    },
    validateMaterials: async (state: AnalysisWorkflowState) => {
      const findings = evaluateClaimRules(state.claim);
      store.update(state.taskId, { findings });
      store.emit(state.taskId, 'tool', 'Tool · validateMaterials', `确定性规则命中 ${findings.length} 个疑点`, findings);
      return { findings };
    },
    retrieveClauses: async (state: AnalysisWorkflowState) => {
      const citations = clauses.search(state.claim.productCode, state.claim.clauseVersion, state.findings);
      store.update(state.taskId, { citations });
      store.emit(state.taskId, 'tool', 'Tool · searchClauses', `按险种 ${state.claim.productCode} / 版本 ${state.claim.clauseVersion} 检索到 ${citations.length} 条依据`, citations);
      return { citations };
    },
    humanReview: async (state: AnalysisWorkflowState) => {
      const review = interrupt({ taskId: state.taskId, findings: state.findings }) as Review;
      return { review };
    },
    generateReport: async (state: AnalysisWorkflowState) => {
      if (state.review?.decision === 'reject') {
        store.update(state.taskId, { status: 'rejected', review: state.review });
        store.emit(state.taskId, 'status', '审核已驳回', state.review.comment);
        return {};
      }
      const report = buildPrototypeReport(state);
      store.update(state.taskId, { status: 'completed', report, review: state.review });
      store.emit(state.taskId, 'report', '分析报告已生成', report.recommendation, report);
      return { report };
    }
  };
}

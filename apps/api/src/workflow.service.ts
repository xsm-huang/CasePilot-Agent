import { ConflictException, Inject, Injectable } from '@nestjs/common';
import { Command } from '@langchain/langgraph';
import type { ClaimCase } from './domain.js';
import { ClauseRepository } from './clause.repository.js';
import { AnalysisStore } from './analysis.store.js';
import { createPrototypeGraph } from './workflow/graph.js';
import type { Review } from './workflow/state.js';

@Injectable()
export class WorkflowService {
  private readonly graph;

  constructor(
    @Inject(ClauseRepository) clauses: ClauseRepository,
    @Inject(AnalysisStore) private readonly store: AnalysisStore
  ) {
    this.graph = createPrototypeGraph(store, clauses);
  }

  async start(taskId: string, claim: ClaimCase): Promise<void> {
    try {
      await this.graph.invoke({ taskId, caseId: claim.id, claim, findings: [], citations: [] }, this.config(taskId));
      await this.publishInterrupt(taskId);
    } catch (error) {
      this.fail(taskId, error);
    }
  }

  async resume(taskId: string, review: Review): Promise<void> {
    if (this.store.get(taskId).status !== 'waiting_review') {
      throw new ConflictException('只有等待审核的任务可以提交审核。');
    }
    try {
      this.store.update(taskId, { status: 'running', review });
      this.store.emit(taskId, 'status', review.decision === 'approve' ? '审核通过，恢复执行' : '审核驳回，恢复执行', review.comment);
      await this.graph.invoke(new Command({ resume: review }), this.config(taskId));
      await this.publishInterrupt(taskId);
    } catch (error) {
      this.fail(taskId, error);
    }
  }

  private config(taskId: string) {
    return { configurable: { thread_id: taskId } };
  }

  private async publishInterrupt(taskId: string): Promise<void> {
    const snapshot = await this.graph.getState(this.config(taskId));
    if (snapshot.next.includes('human_review')) {
      this.store.update(taskId, { status: 'waiting_review' });
      this.store.emit(taskId, 'review_required', '需要人工审核', '规则发现疑点。审核仅决定是否继续分析，不代表赔付审批。', this.store.get(taskId).findings);
    }
  }

  private fail(taskId: string, error: unknown): void {
    const message = error instanceof Error ? error.message : String(error);
    this.store.update(taskId, { status: 'failed' });
    this.store.emit(taskId, 'error', '工作流执行失败', message);
  }
}

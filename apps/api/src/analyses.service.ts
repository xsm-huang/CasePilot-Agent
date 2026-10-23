import { Inject, Injectable } from '@nestjs/common';
import { AnalysisStore } from './analysis.store.js';
import { CasesService } from './cases.service.js';
import { WorkflowService } from './workflow.service.js';
import type { Review } from './workflow/state.js';

/** V0 application operations. Controllers only validate/translate transport values. */
@Injectable()
export class AnalysesService {
  constructor(
    @Inject(AnalysisStore) private readonly store: AnalysisStore,
    @Inject(CasesService) private readonly cases: CasesService,
    @Inject(WorkflowService) private readonly workflow: WorkflowService
  ) {}

  list() {
    return this.store.list();
  }

  get(id: string) {
    return this.store.get(id);
  }

  create(caseId: string) {
    const claim = this.cases.get(caseId);
    const task = this.store.create(claim.id);
    setImmediate(() => { void this.workflow.start(task.id, claim); });
    return task;
  }

  async review(id: string, review: Review) {
    await this.workflow.resume(id, review);
    return { accepted: true, taskId: id };
  }

  events(id: string, after: number) {
    return this.store.events(id, after);
  }
}

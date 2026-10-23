import { Module } from '@nestjs/common';
import { CasesController } from './cases.controller.js';
import { AnalysesController } from './analyses.controller.js';
import { AnalysisStore } from './analysis.store.js';
import { ClauseRepository } from './clause.repository.js';
import { WorkflowService } from './workflow.service.js';
import { CasesService } from './cases.service.js';
import { AnalysesService } from './analyses.service.js';

@Module({
  controllers: [CasesController, AnalysesController],
  providers: [AnalysisStore, ClauseRepository, WorkflowService, CasesService, AnalysesService]
})
export class AppModule {}

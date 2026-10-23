import { Module } from "@nestjs/common";
import { CasesController } from "./cases.controller.js";
import { AnalysesController } from "./analyses.controller.js";
import { AnalysisStore } from "./analysis.store.js";
import { ClauseRepository } from "./clause.repository.js";
import { WorkflowService } from "./workflow.service.js";
import { CasesService } from "./cases.service.js";
import { AnalysesService } from "./analyses.service.js";

/**
 * CasesController：案件接口
 * AnalysesController：分析任务接口
 * AnalysisStore：内存任务存储
 * ClauseRepository：条款检索
 * WorkflowService：LangGraph 工作流
 * CasesService：案件查询
 * AnalysesService：分析任务业务操作
 */
@Module({
  controllers: [CasesController, AnalysesController],
  providers: [
    AnalysisStore,
    ClauseRepository,
    WorkflowService,
    CasesService,
    AnalysesService,
  ],
})
export class AppModule {}

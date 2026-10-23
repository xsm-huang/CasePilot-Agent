# CasePilot Agent

真实运行 Vue 3、NestJS、LangGraph.js 的图执行、interrupt/Command 恢复与 SSE；案件/条款为虚构示例，检索使用内存关键词匹配，报告为确定性模板。尚未接入大模型、LangChain 文档解析、Embedding 或 pgvector，因此不应将这一版描述为完整 AI/RAG 实现。

## MVP 验证闭环

1. 从预置案件中选择一件并启动分析。
2. Agent 查询案件、校验材料，并用确定性规则识别材料缺失和跨来源冲突。
3. 按疑点检索相关保险条款，返回可溯源的条款编号与原文。
4. 命中任何疑点的案件在报告生成前暂停，等待人工审核；无疑点案件直接生成报告。
5. 审核通过后从断点恢复，生成结构化案件分析报告。
6. 前端通过 SSE 实时展示节点状态、工具调用和完整执行时间线。
7. 支持切换案件、选择历史任务、刷新恢复、审核驳回、重复审核保护和基础事件重放。

完整操作与状态流转见 [项目功能流程说明](docs/FUNCTIONAL_FLOW.md)，功能范围见 [功能拆解与迭代计划](docs/MVP.md)，接口与演示步骤见 [原型使用说明](docs/PROTOTYPE.md)。

V1 已按 [设计文档](docs/V1_DESIGN.md) 开始 G0 准备与验证，附 [接口与事件契约](docs/V1_CONTRACTS.md) 和 [测试验收方案](docs/V1_ACCEPTANCE.md)。当前业务应用仍为 V0；V1 的实施目标不等于功能已通过验收。

## V1 本地环境准备

项目根目录 `.env` 是不跟踪的本地配置，模板为 `.env.example`。在本地填写 `ZHIPU_API_KEY`，同一个智谱标准 API Key 用于 `glm-4.7-flash` 和 `embedding-3`，不要把实际密钥发到聊天或提交到仓库。

```bash
pnpm db:up
pnpm db:status
```

Docker 项目名称为 `casepilot-agent`，数据库仅绑定 `127.0.0.1:15432`，使用独立数据卷，避免与其他项目常用的 5432 端口冲突。首次初始化启用 pgvector；停止数据库可执行 `pnpm db:stop`，不会删除数据卷。

真实服务最小探测已通过：`glm-4.7-flash` 工具调用与 JSON 输出、`embedding-3` 的 1024 维向量。数据库、pgvector 和官方 PostgresSaver 已初始化，两个独立进程的 checkpoint 写入、读取与中断恢复探测通过。业务工作台仍为 V0，尚未接入这些能力；探测成功不等于完整案件持久恢复或 V1 完成。进展见 [实施与验证记录](docs/V1_IMPLEMENTATION_STATUS.md)。

需要重新验证凭据时，手动执行 `pnpm model:probe`。它最多发送三次小请求，可能消耗模型额度；不会自动重试，也不会输出密钥。仅检查本地配置与数据库可执行 `node scripts/check-v1-setup.mjs`；该脚本不调用模型，也不会独立宣告完整 G0 通过。

## 运行

已验证环境：Node.js 24.16、pnpm 12.4.2。无需模型 API Key、Docker 或数据库。

```bash
pnpm install
pnpm dev
```

- 工作台：http://127.0.0.1:5173
- API：http://localhost:3000/api

## 验证

```bash
pnpm test
pnpm test:setup
pnpm build
```

保持 `pnpm dev` 运行，在另一终端执行 `pnpm smoke`，验证真实 HTTP 请求、SSE 增量事件与审核恢复。

也可在 `pnpm build` 后执行 `pnpm smoke:isolated`：脚本使用临时端口启动自己的 API 进程，完成同一组 HTTP/SSE 检查后关闭该进程，不触碰已运行的开发服务。

后端目前使用内存存储：页面刷新可以恢复，**API 进程重启会清空全部任务与 checkpoint**。开发模式修改后端源码也会触发重启。

预置的 `CASE-2026-001` 会命中“事故日期早于保单生效日期”和“维修发票缺失”，因此工作流会暂停等待审核；通过审核后生成带条款引用的报告。

`CASE-2026-002` 材料齐全且日期有效，会跳过人工审核直接生成报告。

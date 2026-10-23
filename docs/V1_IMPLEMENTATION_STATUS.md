# V1 实施与验证记录

日期：2026-10-23。用户已批准按设计实施，分析模型与 Embedding 均使用智谱。

本文件只记录已经完成的准备和验证；[设计](V1_DESIGN.md)、[契约](V1_CONTRACTS.md)、[验收矩阵](V1_ACCEPTANCE.md) 仍是实现与验收依据。

## 当前门禁

G0 已通过：配置、数据库、真实模型能力以及官方 PostgresSaver 跨进程中断恢复已分别验证。主代理重新执行真实模型探测成功：`glm-4.7-flash` 工具调用与 JSON 输出通过，`embedding-3` 实际返回 1024 维；验证时间为 `2026-10-22T17:31:59.559Z`（北京时间 2026-10-23 01:31:59）。模型认证已不再是当前卡点。

G1 结构整理已实现并完成构建、回归及可读性交叉评审。G2～G5 业务和联合验收尚未完成；没有使用 V0 模板、固定向量或 stub 代替真实模型通过验收。

G0 的 PostgresSaver 探测使用独立测试图和两个进程，证明基础持久能力；当前案件业务图仍使用 V0 MemorySaver 和内存任务，不能据此宣称案件已经支持跨进程恢复。

## 测试人员实测

| 命令 | 结果 | 证据范围 |
| --- | --- | --- |
| `pnpm test` | 通过，3 文件、7 用例 | V0 规则、关键词条款库、进程内 LangGraph 审核流程；不证明 V1 RAG 或持久恢复 |
| `node --test tests/setup/*.test.mjs` | 通过，5 用例 | 准备检查只输出 boolean，缺密钥/错误维度/错误数据库配置被识别；Docker 命令限定项目，错误不泄露凭据；Docker 为测试替身 |
| `pnpm --filter @casepilot/api exec tsx --test ../../tests/setup/model-config.test.ts` | 阻塞，未执行测试 | pnpm 隐式尝试同步 workspace 依赖时，删除 `node_modules/.pnpm` 被拒绝；已停止并通知协调者统一处理 |
| `node --experimental-transform-types --test tests/setup/model-config.test.ts` | 通过，4 用例 | 使用现有 Node 24 运行配置边界检查，无需安装依赖；检查固定模型/1024维、缺密钥、非官方地址和非法数字；存在 Node 实验功能提示 |
| `node --experimental-transform-types --test tests/setup/capability-probe.test.ts` | 通过，6 用例 | fetch 测试替身验证三请求成功、401 错误脱敏、无 Tool、非法 JSON、错维度、超时；不重试、不跟随重定向，测试后自动恢复 fetch；不代表真实服务质量 |
| `node --experimental-transform-types --test tests/setup/request-scope.test.ts` | 通过，2 用例 | 前端纯作用域切换会中断旧请求并使旧闭包失效；销毁后迟到结果无效；尚不证明 composable 的全部回调已正确接线 |
| `node --experimental-transform-types --test tests/setup/analysis-events.test.ts` | 通过，4 用例 | V0 连续事件不可变归并、重复去重、序号缺口、审核/报告 Schema 校验及坏 payload 失败 |
| `pnpm test:setup` | 通过，21 用例（5 个 mjs＋16 个 TS） | 汇总上述准备、配置、模型探测替身、作用域和事件归并确定性检查，不发真实请求 |
| `node scripts/smoke-isolated.mjs` | 通过 | 从编译产物启动自有临时 API 进程，使用独立空闲端口运行 HTTP/SSE 冒烟：输入验证、审核暂停/通过/驳回、重复审核防护、正常案件、实时事件及游标重放；完成后仅停止自有子进程，不复用或停止用户现有 API |

真实模型探测成功后重新执行以上 V0 回归和两组配置测试：7＋5＋4 项再次通过。没有在测试命令中发起模型请求。

新增 `scripts/check-v1-setup.mjs` 为只读检查：读取项目根 `.env` 和进程环境，验证必填配置，通过 Docker 命令检查 `casepilot-agent` 的 `postgres` 服务及 vector 扩展/运算符。它不调用外部模型，不创建容器，不修改数据库，不打印环境变量值或命令原始错误。

`setupReady` 只表示配置与数据库准备完成；`providerCapabilitiesVerified`、`checkpointPersistenceVerified` 和 `g0Passed` 不会因为准备检查成功而标为 true。完整门禁结果需要独立真实集成证据。

## 主代理提供的集成实测证据

以下结果来自主代理本轮执行与回报；测试人员本次仅更新记录，没有读取 `.env` 或重复发送真实请求。

| 检查 | 结果 | 证据范围 |
| --- | --- | --- |
| `docker compose up -d --wait postgres` | 通过 | `casepilot-agent-postgres-1` 健康；监听 `127.0.0.1:15432`；数据库 `casepilot`，vector 扩展版本 0.8.7；原 `rule-workbench` 未修改 |
| `pnpm install` | 通过 | 依赖安装已完成，先前 pnpm 隐式同步权限问题不再是当前卡点 |
| contracts 构建 | 通过 | 共享契约包可构建；不代表全部 V1 API 和事件 Schema 已实现 |
| `check-v1-setup` | 配置和数据库准备通过 | `setupReady=true`；`providerCapabilitiesVerified=false`、`checkpointPersistenceVerified=false`、`g0Passed=false` |
| Key 安全格式检查 | 通过 | 未发现 Bearer 前缀、空白或非 ASCII 字符；格式通过不能证明凭据有效 |
| `model:probe` | 失败，HTTP 401 | 在沙箱外发送首个真实请求即认证失败；工具调用未通过，结构化输出和 Embedding 两项未执行；没有静默重试或回退 |
| `model:probe` 后续重试 | 通过，`verified=true` | 实际 `glm-4.7-flash` 工具调用和 JSON 输出、`embedding-3` 1024 维通过；`checkedAt=2026-10-22T17:31:59.559Z`；先前 HTTP 401 已解除 |
| 数据库 probe 写进程 | 通过 | 独立临时 schema 中执行迁移与官方 checkpoint 初始化，`migrationVersion=1`、`waitingReview=true` |
| 数据库 probe 读进程 | 通过 | 第二进程输出 `crossProcessRead=true`、`interruptResume=true`、`probeCleaned=true`；临时探测 schema 已清理，业务/checkpoint schema 保留；checkpoint 包 1.1.2、pg 8.23.1 |
| `pnpm build` | 通过 | 全工作区共享契约、API、Vue 类型检查及 Vite 构建通过 |
| `pnpm test`（G1 拆分后） | 通过，7 用例 | 原 V0 图行为保持；不等同于 V1 业务图已经接入真实模型或数据库 |

## 尚未执行

- Token/额度核对及调用预算确认；小型能力探测不能替代后续真实 Agent/RAG 质量验收。
- 将已验证的数据库/checkpointer 基础能力接入案件业务持久状态，并完成真实业务恢复验收。
- V1 条款导入、检索、报告、多轮对话、前端与联合验收。

## G1 验收准备

G1 交叉评审与回归结果如下，边界限定为保留 V0 行为的结构整理。

| 检查 | 计划证据 | 当前状态 |
| --- | --- | --- |
| V0 行为保持 | 缺件/日期规则、审核通过/驳回、同任务恢复、不同任务隔离的既有回归 | 拆分前后均通过，7 用例 |
| 前端事件归并 | 重复去重、缺口拒绝、不可变更新、报告/审核 payload 验证 | 4 项纯函数测试通过；真实 V1 分节报告和终态协议留待 G4 |
| 前端过期请求 | A→B 切换后，A 的成功、失败、finally 和 SSE 回调均不能写入 B | 2 项作用域测试通过；静态审查 useWorkbench 的 success/catch/finally 均有 isCurrent，SSE 绑定 source＋作用域＋taskId；浏览器快切故障注入待 G4 |
| 后端拆分边界 | 图、节点、规则、报告、应用服务和传输职责可独立理解 | 静态评审通过：graph 只定义编排，nodes 执行业务，report 纯函数；CasesService/AnalysesService 承担应用操作，Controller 处理 HTTP 输入与映射 |
| 类型与构建 | 共享契约、前后端构建；边界使用共享 DTO/Schema | 全工作区构建通过；V0 传输契约显式保留，完整 V1 任务及事件 Schema 尚待后续 |

可读性评审未发现 G1 阻断问题。前端当前采用任务绑定的案件副本，尚无服务端历史 `caseSnapshot`；这只能防止选择错位，不能证明历史案件版本恢复。后端节点中现有 Tool 文案、关键词检索与模板报告仍属于 V0，真实 LangChain Tools、RAG 和模型报告按后续门禁实现。

本记录中的通过项不能合并称为“V1 已完成”。

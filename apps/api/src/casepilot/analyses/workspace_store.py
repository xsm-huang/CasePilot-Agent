"""V1 task projections and atomic business updates; legacy tasks are read-only."""

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid4, uuid5

from ..persistence.workspace_repository import WorkspaceRepository
from .errors import AnalysisError
from .store import Store

ACTIVE = {"queued", "running", "waiting_review", "resuming", "recoverable"}
TERMINAL = {"completed", "rejected", "failed"}
CONTEXT_FIELDS = (
    "caseVersion",
    "generationId",
    "embeddingProfile",
    "messageIds",
    "modelProfile",
    "promptVersion",
)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def fingerprint(body):
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def stable_id(task_id, key):
    return str(uuid5(NAMESPACE_URL, f"casepilot:{task_id}:{key}"))


class WorkspaceStore(Store):
    def __init__(self, pool=None, schema="casepilot_python"):
        super().__init__(pool, schema)
        self.repository = WorkspaceRepository(pool, self.schema) if pool else None
        self.conversations = {}

    async def setup(self):
        await super().setup()
        if any(
            t.get("schemaVersion") != 1 and t["status"] not in TERMINAL for t in self.tasks.values()
        ):
            raise RuntimeError(
                "Active legacy tasks prevent V1 cutover; finish or explicitly migrate them first"
            )
        if self.repository:
            self.conversations = await self.repository.conversations()

    def require_database(self):
        if not self.repository:
            raise AnalysisError(
                "DEPENDENCY_UNAVAILABLE", "新分析需要 PostgreSQL，请先启用持久存储。"
            )

    def conversation(self, conversation_id):
        if conversation_id not in self.conversations:
            raise AnalysisError("NOT_FOUND", "会话不存在。")
        return deepcopy(self.conversations[conversation_id])

    def active_task(self, conversation_id):
        return next(
            (
                t
                for t in self.tasks.values()
                if t.get("conversationId") == conversation_id and t["status"] in ACTIVE
            ),
            None,
        )

    def summary(self, conversation):
        result = {
            key: conversation[key] for key in ("id", "caseId", "title", "createdAt", "updatedAt")
        }
        active = self.active_task(conversation["id"])
        return result | {"activeAnalysisId": active["id"] if active else None}

    @staticmethod
    def public(task):
        result = {key: deepcopy(value) for key, value in task.items() if not key.startswith("_")}
        if task.get("schemaVersion") == 1:
            result.pop("events", None)
        else:
            result.update(schemaVersion=0, readOnly=True)
        return result

    def writable(self, task_id):
        task = self.get(task_id)
        if task.get("schemaVersion") != 1:
            raise AnalysisError("LEGACY_READ_ONLY", "旧版模板报告只读，不能审核或继续执行。")
        return task

    def append(self, task, event_type, data, key):
        if key in task["_effects"]:
            return False
        task["revision"] += 1
        payload = deepcopy(data)
        if "revision" in payload:
            payload["revision"] = task["revision"]
        event = {
            "schemaVersion": 1,
            "analysisId": task["id"],
            "conversationId": task["conversationId"],
            "seq": task["lastEventSeq"] + 1,
            "revision": task["revision"],
            "at": now(),
            "type": event_type,
            "data": payload,
        }
        task["events"].append(event)
        task["lastEventSeq"] = event["seq"]
        task["_effects"].append(key)
        if event_type.startswith(("node.", "tool.")):
            collection = task["execution"]["tools" if event_type.startswith("tool.") else "nodes"]
            previous = next(
                (
                    i
                    for i, item in enumerate(collection)
                    if item["executionId"] == payload["executionId"]
                ),
                None,
            )
            if previous is None:
                collection.append(payload)
            else:
                collection[previous] = payload
        task["execution"]["timeline"] = deepcopy(task["events"])
        return True

    def project_agent_call(self, task, call_key, call):
        status = call["status"]
        tool = call["kind"] in {"local", "retrieval"}
        phase = (
            "started" if status == "reserved" else "failed" if status == "failed" else "completed"
        )
        elapsed = max(
            0,
            int(
                (
                    datetime.now(timezone.utc) - datetime.fromisoformat(call["startedAt"])
                ).total_seconds()
                * 1000
            ),
        )
        payload = {
            "executionId": stable_id(task["id"], call_key),
            "key": call_key,
            "name": self.call_name(call_key.rsplit(":", 1)[0]),
            "attempt": int(call_key.rsplit(":", 1)[1]),
            "status": "running" if status == "reserved" else status,
            "summary": "执行中"
            if status == "reserved"
            else "已完成"
            if status == "completed"
            else "执行失败",
            "durationMs": elapsed,
        }
        self.append(
            task, f"{'tool' if tool else 'node'}.{phase}", payload, f"call:{call_key}:{status}"
        )

    @staticmethod
    def call_name(key):
        labels = {
            "tool:query_case": "查询案件",
            "tool:validate_materials": "核验事实与材料",
            "retrieval:initial": "检索条款依据",
            "model:assessment": "生成结构化分析",
            "model:report:summary": "生成案件摘要",
            "model:report:findings": "生成疑点与依据",
            "model:report:recommendations": "生成处理建议",
        }
        if key.endswith(":repair"):
            return WorkspaceStore.call_name(key.removesuffix(":repair")) + "（结构修复）"
        if key.startswith("model:decision:"):
            return "判断是否需要补充检索"
        if key.startswith("retrieval:") and key != "retrieval:initial":
            return "补充检索条款"
        return labels.get(key, "执行分析步骤")

    async def create_conversation(self, case_id, title):
        self.require_database()
        conversation = {
            "id": str(uuid4()),
            "caseId": case_id,
            "title": title,
            "createdAt": now(),
            "updatedAt": now(),
            "context": None,
        }
        async with self.lock:
            await self.repository.save_conversation(conversation)
            self.conversations[conversation["id"]] = conversation
        return self.summary(conversation)

    async def create_analysis(self, body, context, history, key, digest):
        conversation_id = body["conversationId"]
        scope = f"create:{conversation_id}"
        async with self.lock:
            previous = await self.repository.request(scope, key, digest)
            if previous:
                return previous
            conversation = self.conversation(conversation_id)
            if self.active_task(conversation_id):
                raise AnalysisError(
                    "ACTIVE_ANALYSIS_EXISTS", "当前会话已有活动任务，请先完成审核或恢复。"
                )
            if conversation["context"] is not None and conversation["context"] != context:
                raise AnalysisError("RECOVERY_CONFLICT", "会话上下文已变化，请重新读取会话。")
            completed = [
                t
                for t in self.tasks.values()
                if t.get("conversationId") == conversation_id and t["status"] == "completed"
            ]
            if body["kind"] == "followup" and not completed:
                raise AnalysisError("INVALID_INPUT", "完成首轮分析后才能继续追问。")
            if body["kind"] == "initial" and completed:
                raise AnalysisError("INVALID_INPUT", "已有完成回合，请使用追问或新建会话。")
            task_id, message_id = str(uuid4()), str(uuid4())
            question = body["question"]
            agent_context = context | {
                "question": question,
                "history": history,
                "messageIds": [m["id"] for m in history],
            }
            task = {
                "schemaVersion": 1,
                "id": task_id,
                "caseId": conversation["caseId"],
                "conversationId": conversation_id,
                "kind": body["kind"],
                "question": question,
                "status": "queued",
                "caseSnapshot": context["caseSnapshot"],
                "revision": 0,
                "lastEventSeq": 0,
                "userMessageId": message_id,
                "assistantMessageId": None,
                "context": {
                    field: agent_context.get(field, [])
                    if field == "messageIds"
                    else agent_context[field]
                    for field in CONTEXT_FIELDS
                },
                "facts": [],
                "ruleFindings": [],
                "modelFindings": [],
                "citations": [],
                "sections": [],
                "report": None,
                "pendingReview": None,
                "execution": {"nodes": [], "tools": [], "timeline": []},
                "error": None,
                "events": [],
                "_effects": [],
                "_artifacts": {},
                "_agent": {
                    "context": agent_context,
                    "calls": {},
                    "counts": {"model": 0, "retrieval": 0, "repair": 0},
                },
            }
            self.append(task, "analysis.status", {"status": "queued", "revision": 0}, "created")
            command = {"id": str(uuid4()), "taskId": task_id, "kind": "start", "status": "pending"}
            message = {
                "id": message_id,
                "role": "user",
                "content": question,
                "analysisId": task_id,
                "createdAt": now(),
            }
            conversation.update(context=deepcopy(context), updatedAt=now())
            response = self.public(task)
            await self.repository.commit(
                task,
                command=command,
                message=message,
                conversation=conversation,
                request=(scope, key, digest, response),
            )
            self.tasks[task_id] = task
            self.commands[command["id"]] = command
            self.conversations[conversation_id] = conversation
            return response

    async def edit(self, task_id, update):
        async with self.lock:
            task = self.writable(task_id)
            update(task)
            await self.repository.save(task)
            self.tasks[task_id] = task
            return self.get(task_id)

    async def start(self, task_id, phase="start"):
        def update(task):
            task.update(status="running", error=None)
            self.append(
                task,
                "analysis.status",
                {"status": "running", "revision": 0},
                f"running:{phase}:{task.get('_run', 0)}",
            )

        return await self.edit(task_id, update)

    async def analysis_ready(self, task_id, result):
        def update(task):
            task["_artifacts"]["analysis"] = deepcopy(result)
            task.update(
                facts=result["facts"],
                ruleFindings=result["ruleFindings"],
                modelFindings=result["modelAnalysis"]["findings"],
                citations=result["citations"],
            )
            self.append(
                task,
                "analysis.ready",
                {
                    "facts": task["facts"],
                    "ruleFindings": task["ruleFindings"],
                    "modelFindings": task["modelFindings"],
                    "citations": task["citations"],
                    "insufficientEvidence": result["modelAnalysis"]["insufficientEvidence"],
                },
                "analysis-ready",
            )

        return await self.edit(task_id, update)

    async def waiting_review(self, task_id, checkpoint_id):
        def update(task):
            if "review-required" in task["_effects"]:
                return
            task["status"] = "waiting_review"
            pending = {
                "interruptKey": stable_id(task_id, "review:1"),
                "checkpointId": checkpoint_id,
                "revision": 0,
                "reason": "请核查规则疑点、模型推断或不足的依据。",
            }
            self.append(task, "review.required", pending, "review-required")
            task["pendingReview"] = task["events"][-1]["data"]

        return await self.edit(task_id, update)

    async def accept(self, task_id, body, key, *, recover=False):
        self.require_database()
        scope = f"{'recover' if recover else 'review'}:{task_id}"
        digest = fingerprint(body)
        async with self.lock:
            cached = await self.repository.request(scope, key, digest)
            if cached:
                return cached
            task = self.writable(task_id)
            if task["revision"] != body["expectedRevision"]:
                raise AnalysisError("REVIEW_CONFLICT", "任务版本已变化，请刷新后重新确认。")
            if recover:
                if task["status"] != "recoverable":
                    raise AnalysisError("RECOVERY_CONFLICT", "该任务不处于可恢复状态。")
                attempts = task["_agent"].setdefault("attempts", {})
                for call_key, call in task["_agent"]["calls"].items():
                    if call["status"] != "completed":
                        logical, attempt = call_key.rsplit(":", 1)
                        attempts[logical] = max(attempts.get(logical, 1), int(attempt) + 1)
                task.update(status="queued", error=None)
                task["_run"] = task.get("_run", 0) + 1
                self.append(
                    task,
                    "analysis.status",
                    {"status": "queued", "revision": 0},
                    f"recover:{task['_run']}",
                )
                payload, review = {"kind": "recover"}, None
            else:
                pending = task["pendingReview"]
                if (
                    task["status"] != "waiting_review"
                    or not pending
                    or pending["interruptKey"] != body["interruptKey"]
                ):
                    raise AnalysisError("REVIEW_CONFLICT", "审核点已失效，请刷新后重新确认。")
                review = deepcopy(body)
                task.update(status="resuming", pendingReview=None, _review=review)
                self.append(
                    task,
                    "review.accepted",
                    {
                        "interruptKey": body["interruptKey"],
                        "decision": body["decision"],
                        "revision": 0,
                    },
                    "review-accepted",
                )
                payload = {"kind": "review", "review": review}
            command = {"id": str(uuid4()), "taskId": task_id, **payload, "status": "pending"}
            response = {"accepted": True, "taskId": task_id, "revision": task["revision"]}
            await self.repository.commit(
                task, command=command, review=review, request=(scope, key, digest, response)
            )
            self.tasks[task_id] = task
            self.commands[command["id"]] = command
            return response

    async def section(self, task_id, key, output):
        def update(task):
            if f"section:{key}" in task["_effects"]:
                return
            section = {"sectionKey": key, **output, "committedAt": now()}
            task["sections"].append(section)
            self.append(task, "report.section", section, f"section:{key}")

        return await self.edit(task_id, update)

    async def reject(self, task_id):
        def update(task):
            task.update(status="rejected", report=None)
            self.append(
                task,
                "analysis.rejected",
                {"comment": task["_review"]["comment"], "revision": 0},
                "rejected",
            )

        return await self.edit(task_id, update)

    async def finalize(self, task_id):
        async with self.lock:
            task = self.writable(task_id)
            if task["status"] == "completed":
                return task
            if [s["sectionKey"] for s in task["sections"]] != [
                "summary",
                "findings",
                "recommendations",
            ]:
                raise AnalysisError("OUTPUT_VALIDATION_FAILED", "报告章节尚未完整验证。")
            message_id = stable_id(task_id, "assistant-message")
            task.update(
                status="completed",
                assistantMessageId=message_id,
                error=None,
                report={
                    "caseId": task["caseId"],
                    "sections": task["sections"],
                    "insufficientEvidence": task["_artifacts"]["analysis"]["modelAnalysis"][
                        "insufficientEvidence"
                    ],
                    "reviewerComment": task.get("_review", {}).get("comment"),
                },
            )
            self.append(
                task,
                "report.completed",
                {"report": task["report"], "assistantMessageId": message_id, "revision": 0},
                "completed",
            )
            message = {
                "id": message_id,
                "role": "assistant",
                "content": "\n\n".join(s["content"] for s in task["sections"]),
                "analysisId": task_id,
                "createdAt": now(),
            }
            conversation = self.conversation(task["conversationId"])
            conversation["updatedAt"] = now()
            await self.repository.commit(task, message=message, conversation=conversation)
            self.tasks[task_id] = task
            self.conversations[conversation["id"]] = conversation
            return task

    async def fail(self, task_id, code, *, recoverable):
        def update(task):
            if f"failure:{task.get('_run', 0)}" in task["_effects"]:
                return
            task.update(
                status="recoverable" if recoverable else "failed",
                error={
                    "code": code,
                    "message": "执行中断，请核对依赖后显式恢复。"
                    if recoverable
                    else "执行失败，请核查输入、额度或输出验证结果。",
                    "requestId": str(uuid4()),
                },
                report=None,
                assistantMessageId=None,
            )
            self.append(
                task,
                "analysis.recoverable" if recoverable else "analysis.failed",
                {"error": task["error"], "revision": 0},
                f"failure:{task.get('_run', 0)}",
            )

        return await self.edit(task_id, update)

"""Closed-claim review task projections and atomic business updates."""

import hashlib
import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid4, uuid5

from ..cases.review_repository import _summary
from ..persistence.workspace_repository import WorkspaceRepository
from ..schemas.workspace import WorkspaceEvent
from .checks import NODE_NAMES
from .errors import AnalysisError
from .reports import build_report
from .review import commit_checks, eligibility, new_review, review_status
from .review_actions import ReviewActions, validate_refs
from .store import Store

ACTIVE = {"queued", "running", "waiting_review", "resuming", "recoverable"}
TERMINAL = {"completed", "rejected", "failed"}
CONTEXT_FIELDS = (
    "inputVersion",
    "knowledgeBindings",
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


def operator_id():
    return os.getenv("CASEPILOT_OPERATOR_ID", "").strip() or "unidentified_operator"


class WorkspaceStore(ReviewActions, Store):
    def __init__(self, pool=None, schema="casepilot_python"):
        super().__init__(pool, schema)
        self.repository = WorkspaceRepository(pool, self.schema) if pool else None
        self.conversations = {}

    def get(self, task_id):
        task = super().get(task_id)
        task["_expectedDbRevision"] = task["revision"]
        return task

    async def setup(self):
        await super().setup()
        self.tasks = {
            key: value
            for key, value in self.tasks.items()
            if value.get("schemaVersion") == 2
            and value.get("reviewState", {}).get("reviewModelVersion") == 1
        }
        self.commands = {
            key: value for key, value in self.commands.items() if value.get("taskId") in self.tasks
        }
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
        result.pop("events", None)
        result["operatorId"] = operator_id()
        result["caseSummary"] = _summary(task["caseSnapshot"]["payload"])
        result["finalizationEligibility"] = eligibility(task)
        result["reviewStatus"] = review_status(task)
        return result

    def writable(self, task_id):
        task = self.get(task_id)
        if task.get("schemaVersion") != 2:
            raise AnalysisError("ANALYSIS_NOT_FOUND", "分析任务不存在。")
        return task

    def append(self, task, event_type, data, key):
        if key in task["_effects"]:
            return False
        task["revision"] += 1
        payload = deepcopy(data)
        if "revision" in payload:
            payload["revision"] = task["revision"]
        event = {
            "schemaVersion": 2,
            "analysisId": task["id"],
            "conversationId": task["conversationId"],
            "seq": task["lastEventSeq"] + 1,
            "revision": task["revision"],
            "at": now(),
            "type": event_type,
            "data": payload,
        }
        event = WorkspaceEvent.model_validate(event).model_dump(mode="json")
        task["events"].append(event)
        task["lastEventSeq"] = event["seq"]
        task["_effects"].append(key)
        if event_type.startswith("tool."):
            collection = task["execution"]["tools"]
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
            "nodeKey": call["nodeKey"],
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
            "kind": call["kind"],
            "parentNodeRunId": call["parentNodeRunId"],
        }
        self.append(task, f"tool.{phase}", payload, f"call:{call_key}:{status}")

    @staticmethod
    def call_name(key):
        if key.startswith("check:"):
            return NODE_NAMES[key.split(":")[1]]
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
        if key.startswith("model:assessment:"):
            return NODE_NAMES[key.split(":")[2]] + " · AI 核对"
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
            predecessor_id = body.get("predecessorAnalysisId")
            if predecessor_id:
                predecessor = self.get(predecessor_id)
                if predecessor["caseId"] != conversation["caseId"]:
                    raise AnalysisError("INVALID_INPUT", "前序任务不属于当前案件。")
            task_id, message_id = str(uuid4()), str(uuid4())
            question = body["question"]
            agent_context = context | {
                "question": question,
                "history": history,
                "messageIds": [m["id"] for m in history],
            }
            task = {
                "schemaVersion": 2,
                "reviewState": new_review(context["caseSnapshot"], task_id),
                "id": task_id,
                "caseId": conversation["caseId"],
                "conversationId": conversation_id,
                "kind": body["kind"],
                "question": question,
                "status": "queued",
                "caseSnapshot": context["caseSnapshot"],
                "predecessorAnalysisId": body.get("predecessorAnalysisId"),
                "evidenceSupplements": [],
                "reviewSupplementIds": [],
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
                "checks": [],
                "reviewHistory": [],
                "reports": [],
                "ruleFindings": [],
                "modelFindings": [],
                "citations": [],
                "sections": [],
                "report": None,
                "pendingReview": None,
                "execution": {"tools": [], "timeline": []},
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
            revision = task["revision"]
            update(task)
            if task["revision"] == revision:
                return self.get(task_id)
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
            commit_checks(task, result.get("checks", []))
            self.append(
                task,
                "analysis.ready",
                {
                    "facts": task["facts"],
                    "ruleFindings": task["ruleFindings"],
                    "modelFindings": task["modelFindings"],
                    "citations": task["citations"],
                    "insufficientEvidence": result["modelAnalysis"]["insufficientEvidence"],
                    "checks": task["checks"],
                },
                "analysis-ready",
            )
            self.review_changed(task)

        return await self.edit(task_id, update)

    async def waiting_review(self, task_id, checkpoint_id):
        def update(task):
            cycle = task["reviewState"]["reviewCycleId"]
            if f"review-required:{cycle}" in task["_effects"]:
                return
            task["status"] = "waiting_review"
            pending = {
                "interruptKey": stable_id(task_id, f"review:{cycle}"),
                "checkpointId": checkpoint_id,
                "revision": 0,
                "reason": "请在各发现节点逐条复核；最终确认检查覆盖和报告内容。",
            }
            self.append(task, "review.required", pending, f"review-required:{cycle}")
            task["pendingReview"] = task["events"][-1]["data"]
            node = next(n for n in task["reviewState"]["businessNodes"] if n["nodeKey"] == "report")
            if node["status"] == "running":
                at = now()
                node.update(
                    status="completed",
                    endedAt=at,
                    durationMs=max(
                        0,
                        int(
                            (
                                datetime.fromisoformat(at)
                                - datetime.fromisoformat(node["startedAt"])
                            ).total_seconds()
                            * 1000
                        ),
                    ),
                    summary=f"汇总 {len(task['checks'])} 项检查及 {sum(f['active'] for f in task['reviewState']['findings'])} 条发现",
                    reason="",
                )
                self.append(
                    task, "business_node.completed", node, f"business:{node['nodeRunId']}:completed"
                )
            self._save_report(task)

        return await self.edit(task_id, update)

    async def accept(self, task_id, body, key, *, recover=False):
        self.require_database()
        if len(body.get("supplementIds", [])) > 20:
            raise AnalysisError("INVALID_INPUT", "一次最多引用 20 份补充证据。")
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
                if task["status"] not in {"recoverable", "waiting_review", "failed"} or not any(
                    n["status"] == "failed" for n in task["reviewState"]["businessNodes"]
                ):
                    raise AnalysisError("RECOVERY_CONFLICT", "该任务不处于可恢复状态。")
                attempts = task["_agent"].setdefault("attempts", {})
                for call_key, call in task["_agent"]["calls"].items():
                    if call["status"] != "completed":
                        logical, attempt = call_key.rsplit(":", 1)
                        attempts[logical] = max(attempts.get(logical, 1), int(attempt) + 1)
                task.update(status="queued", error=None)
                task["_artifacts"].pop("analysis", None)
                task.pop("_review", None)
                task["pendingReview"] = None
                task["reviewState"]["reviewCycleId"] += 1
                task["_run"] = task.get("_run", 0) + 1
                self.append(
                    task,
                    "analysis.status",
                    {"status": "queued", "revision": 0},
                    f"recover:{task['_run']}",
                )
                payload, review = {"kind": "recover"}, None
            else:
                active = self.active_task(task["conversationId"])
                if active and active["id"] != task_id:
                    raise AnalysisError("REVIEW_CONFLICT", "同一会话已有其他活动任务，请先处理。")
                pending = task["pendingReview"]
                if (
                    task["status"] not in {"waiting_review", "failed", "recoverable"}
                    or not pending
                    or pending["interruptKey"] != body["interruptKey"]
                ):
                    raise AnalysisError("REVIEW_CONFLICT", "审核点已失效，请刷新后重新确认。")
                available = {item["supplementId"] for item in task["evidenceSupplements"]}
                if not set(body.get("supplementIds", [])) <= available:
                    raise AnalysisError("INVALID_INPUT", "审核引用了不属于当前任务的补充证据。")
                selected = [
                    item
                    for item in task["evidenceSupplements"]
                    if item["supplementId"] in body.get("supplementIds", [])
                ]
                if body["decision"] == "approve" and any(
                    item["addedBy"] == "unidentified_operator" for item in selected
                ):
                    raise AnalysisError(
                        "OPERATOR_IDENTITY_REQUIRED",
                        "补充证据的操作者身份未识别，不能据此通过正式审核。",
                    )
                if body["decision"] == "approve":
                    if operator_id() == "unidentified_operator":
                        raise AnalysisError(
                            "OPERATOR_IDENTITY_REQUIRED", "尚未配置当前操作者，不能完成正式审查。"
                        )
                    if (
                        not body.get("coverageConfirmed")
                        or len(body.get("comment", "").strip()) < 5
                    ):
                        raise AnalysisError(
                            "INVALID_INPUT", "请确认检查覆盖及报告内容，并填写具体复核意见。"
                        )
                    if not eligibility(task)["allowed"]:
                        raise AnalysisError(
                            "REVIEW_CONFLICT",
                            "仍有范围内未决或无法完成的检查，请在对应节点处理后再确认。",
                        )
                    if (
                        body["reviewCycleId"] != task["reviewState"]["reviewCycleId"]
                        or body["basisHash"] != eligibility(task)["basisHash"]
                        or not task["report"]
                        or body["reportVersion"] != task["report"]["version"]
                        or body["basisHash"] != task["report"]["basisHash"]
                    ):
                        raise AnalysisError(
                            "REVIEW_CONFLICT", "报告依据已变化，请查看最新报告重新确认。"
                        )
                review = deepcopy(body)
                review.update(operatorId=operator_id(), at=now())
                task.update(
                    status="resuming",
                    pendingReview=None,
                    reviewSupplementIds=body.get("supplementIds", []),
                    _review=review,
                )
                self.append(
                    task,
                    "review.accepted",
                    {
                        "interruptKey": body["interruptKey"],
                        "decision": body["decision"],
                        "revision": 0,
                        "comment": review["comment"],
                        "operatorId": review["operatorId"],
                        "nodeKey": "report",
                    },
                    f"review-accepted:{task['reviewState']['reviewCycleId']}",
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

    async def add_supplement(self, task_id, supplement, key, digest, expected_revision):
        async with self.lock:
            scope = f"supplement:{task_id}"
            cached = await self.repository.request(scope, key, digest)
            if cached:
                return cached
            task = self.writable(task_id)
            if (
                task["status"] not in {"waiting_review", "failed", "recoverable"}
                or task["revision"] != expected_revision
            ):
                raise AnalysisError("REVIEW_CONFLICT", "任务版本或状态已变化，请查看最新记录。")
            if operator_id() == "unidentified_operator":
                raise AnalysisError("OPERATOR_IDENTITY_REQUIRED", "补充证据需要已识别的操作者。")
            task["evidenceSupplements"].append(deepcopy(supplement))
            self.append(
                task,
                "evidence.supplemented",
                {"supplement": supplement, "revision": 0},
                f"supplement:{supplement['supplementId']}",
            )
            self._save_report(task)
            await self.repository.commit(task, request=(scope, key, digest, supplement))
            self.tasks[task_id] = task
            return supplement

    def _save_report(self, task, *, final=False):
        report = build_report(task, now(), final=final)
        if (
            task.get("report")
            and task["report"]["basisHash"] == report["basisHash"]
            and task["report"]["kind"] == report["kind"]
        ):
            return task["report"]
        task.setdefault("reports", []).append(deepcopy(report))
        task["report"] = report
        task["sections"] = report["sections"]
        self.append(task, "report.saved", report, f"report:{report['version']}")
        return report

    async def save_report(self, task_id, *, final=False):
        def update(task):
            if final and (
                not eligibility(task)["allowed"]
                or not task.get("_review", {}).get("coverageConfirmed")
            ):
                raise AnalysisError("REVIEW_CONFLICT", "未满足最终审查完成条件。")
            if final and task.get("report", {}).get("kind") == "final":
                return
            self._save_report(task, final=final)

        return await self.edit(task_id, update)

    async def review_finding(self, task_id, finding_id, body, key):
        self.require_database()
        scope, digest = f"finding:{task_id}:{finding_id}", fingerprint(body)
        async with self.lock:
            cached = await self.repository.request(scope, key, digest)
            if cached:
                return cached
            task = self.writable(task_id)
            if (
                task["status"] not in {"waiting_review", "failed", "recoverable"}
                or task["revision"] != body["expectedRevision"]
            ):
                raise AnalysisError("REVIEW_CONFLICT", "任务状态或版本已变化，请先查看最新记录。")
            item = next(
                (r for r in task["reviewState"]["findings"] if r["findingId"] == finding_id), None
            )
            if not item or body["findingVersion"] != item["version"]:
                raise AnalysisError("INVALID_INPUT", "该事项不是当前任务的待复核发现。")
            if operator_id() == "unidentified_operator":
                raise AnalysisError(
                    "OPERATOR_IDENTITY_REQUIRED", "尚未配置当前操作者，不能保存正式复核意见。"
                )
            if len(body["comment"].strip()) < 5 or body["comment"].strip() in {
                "同意",
                "无问题",
                "确认无问题",
            }:
                raise AnalysisError("INVALID_INPUT", "请填写具体事实、判断理由及依据。")
            for field, allowed in (
                ("factRefs", {f["factId"] for f in task["facts"]}),
                ("citationRefs", {c["citationId"] for c in task["citations"]}),
                ("supplementIds", {s["supplementId"] for s in task["evidenceSupplements"]}),
            ):
                if not set(body.get(field, [])) <= allowed:
                    raise AnalysisError("INVALID_INPUT", "复核引用了不属于当前任务的依据。")
            if body["decision"] in {"confirmed", "excluded"} and not any(
                body.get(f) for f in ("factRefs", "citationRefs", "supplementIds")
            ):
                raise AnalysisError(
                    "INVALID_INPUT", "确认或排除须关联已查看的事实、条款或补充证据。"
                )
            if body["decision"] in {"confirmed", "excluded"}:
                if not body["evidenceViewed"]:
                    raise AnalysisError("EVIDENCE_NOT_VIEWED", "请确认已查看所选依据。")
                validate_refs(task, body, viewed=True)
            if body["decision"] in {"pending", "referred"} and not body["recipient"].strip():
                raise AnalysisError("INVALID_INPUT", "请填写跟进对象或专业接收岗位。")
            if body["decision"] == "pending" and not body["missingItems"].strip():
                raise AnalysisError("INVALID_INPUT", "请填写待补充资料和核实内容。")
            if body["decision"] in {"confirmed", "excluded"} and any(
                s["supplementId"] in body.get("supplementIds", [])
                and s["addedBy"] == "unidentified_operator"
                for s in task["evidenceSupplements"]
            ):
                raise AnalysisError(
                    "OPERATOR_IDENTITY_REQUIRED", "补充材料提交人未识别，不能据此完成正式复核。"
                )
            if (
                body["decision"] in {"confirmed", "pending", "referred"}
                and not body.get("followup", "").strip()
            ):
                raise AnalysisError(
                    "INVALID_INPUT", "请填写后续建议、缺少资料及跟进对象或专业接收岗位。"
                )
            previous = [r for r in task.get("reviewHistory", []) if r["findingId"] == finding_id]
            if body["previousReviewId"] != (previous[-1]["reviewId"] if previous else ""):
                raise AnalysisError("REVIEW_CONFLICT", "本项已有新的人工决定，请查看后再修改。")
            if (
                previous
                and previous[-1]["decision"] == "referred"
                and body["decision"] in {"confirmed", "excluded"}
                and not any(
                    r["kind"] == "professional"
                    and r["targetId"] == finding_id
                    and r["state"] == "opinion_received"
                    for r in task["reviewState"]["records"]
                )
            ):
                raise AnalysisError("INVALID_INPUT", "请先记录专业意见及其来源。")
            if previous and not body.get("changeReason", "").strip():
                raise AnalysisError("INVALID_INPUT", "修改复核结论须填写变更原因。")
            review = {
                k: body.get(k, [] if k.endswith("Refs") or k == "supplementIds" else "")
                for k in (
                    "decision",
                    "comment",
                    "factRefs",
                    "citationRefs",
                    "supplementIds",
                    "followup",
                    "changeReason",
                    "recipient",
                    "missingItems",
                    "findingVersion",
                    "previousReviewId",
                    "evidenceViewed",
                )
            }
            review.update(
                reviewId=str(uuid4()),
                findingId=finding_id,
                nodeKey=item["nodeKey"],
                operatorId=operator_id(),
                at=now(),
            )
            task.setdefault("reviewHistory", []).append(review)
            report = self._save_report(task)
            self.append(
                task,
                "finding.reviewed",
                {"review": review, "report": report, "revision": 0},
                f"review:{review['reviewId']}",
            )
            response = {"accepted": True, "taskId": task_id, "revision": task["revision"]}
            await self.repository.commit(task, request=(scope, key, digest, response))
            self.tasks[task_id] = task
            return response

    async def reject(self, task_id):
        def update(task):
            task.update(status="rejected")
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
            if (
                not task.get("report")
                or task["report"].get("kind") != "final"
                or not eligibility(task)["allowed"]
            ):
                raise AnalysisError("OUTPUT_VALIDATION_FAILED", "最终报告及必要人工复核尚未完成。")
            message_id = stable_id(task_id, "assistant-message")
            task.update(
                status="completed",
                assistantMessageId=message_id,
                error=None,
            )
            self.append(
                task,
                "report.completed",
                {"report": task["report"], "assistantMessageId": message_id, "revision": 0},
                f"completed:{task['reviewState']['reviewCycleId']}",
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
            existing = await self.repository.has_assistant_message(task_id)
            await self.repository.commit(
                task, message=None if existing else message, conversation=conversation
            )
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
            )
            for node in task["reviewState"]["businessNodes"]:
                if node["status"] == "running":
                    node.update(
                        status="failed",
                        endedAt=now(),
                        reason=code,
                        summary="执行中断，保留已提交结果；中断耗时无法完整确认",
                    )
                    self.append(
                        task,
                        "business_node.failed",
                        node,
                        f"interrupted:{node['nodeRunId']}:{task.get('_run', 0)}",
                    )
            task["pendingReview"] = dict(
                interruptKey=stable_id(task_id, f"review:{task['reviewState']['reviewCycleId']}"),
                checkpointId="manual",
                revision=task["revision"],
                reason="自动执行中断，可复核已保存结果。",
            )
            self.append(
                task,
                "analysis.recoverable" if recoverable else "analysis.failed",
                {"error": task["error"], "revision": 0},
                f"failure:{task.get('_run', 0)}",
            )
            self._save_report(task)

        return await self.edit(task_id, update)

"""Small transactional commands for manual review; original AI input stays immutable."""

import os
from copy import deepcopy
from uuid import uuid4

from ..schemas.agent import ReviewCheck
from ..schemas.review import ReviewRecord
from .checks import check
from .errors import AnalysisError
from .review import commit_checks, eligibility, excluded_checks


def actor():
    value = os.getenv("CASEPILOT_OPERATOR_ID", "").strip()
    if not value:
        raise AnalysisError("OPERATOR_IDENTITY_REQUIRED", "当前操作者未识别。")
    return value


def validate_refs(task, body, *, viewed=False):
    allowed = {
        "factRefs": {f["factId"] for f in task["facts"]},
        "citationRefs": {c["citationId"] for c in task["citations"]},
        "supplementIds": {s["supplementId"] for s in task["evidenceSupplements"]},
    }
    selected = set()
    for field, ids in allowed.items():
        refs = set(body.get(field, []))
        if not refs <= ids:
            raise AnalysisError("INVALID_INPUT", "依据不存在或不属于本次审查。")
        selected.update(f"{field}:{ref}" for ref in refs)
    if viewed:
        opened = set()
        for row in task["reviewState"]["records"]:
            if row["kind"] == "evidence_view" and row["operatorId"] == actor():
                for field in allowed:
                    opened.update(f"{field}:{ref}" for ref in row[field])
        if not selected or not selected <= opened:
            raise AnalysisError("EVIDENCE_NOT_VIEWED", "请先查看所选原始依据，再保存人工结论。")
    return bool(selected)


class ReviewActions:
    def review_changed(self, task):
        self.append(task, "review.updated", task["reviewState"], f"review-state:{task['revision']}")

    async def review_write(self, task_id, body, key, action, update):
        from .workspace_store import fingerprint

        self.require_database()
        async with self.lock:
            scope, hashed = f"{action}:{task_id}", fingerprint(body)
            cached = await self.repository.request(scope, key, hashed)
            if cached:
                return cached
            task = self.writable(task_id)
            if task["revision"] != body["expectedRevision"]:
                raise AnalysisError("REVIEW_CONFLICT", "内容已更新，请查看最新记录再操作。")
            if task["status"] in {"queued", "running", "resuming", "rejected"}:
                raise AnalysisError("REVIEW_CONFLICT", "执行中或已终止，不能修改人工审查。")
            actor()
            update(task)
            self.review_changed(task)
            if action != "evidence_view":
                self._save_report(task, final=task["status"] == "completed")
            response = dict(accepted=True, taskId=task_id, revision=task["revision"])
            await self.repository.commit(task, request=(scope, key, hashed, response))
            self.tasks[task_id] = task
            return response

    async def manual_finding(self, task_id, body, key):
        def update(task):
            if task["status"] == "completed":
                raise AnalysisError("REVIEW_CONFLICT", "请先重新打开复核并填写更正原因。")
            if not validate_refs(task, body):
                raise AnalysisError("INVALID_INPUT", "人工发现必须关联原始依据。")
            all_ids = {
                v
                for f in task["facts"]
                if isinstance(f["value"], dict)
                for k, v in f["value"].items()
                if k.endswith("Id") and isinstance(v, str)
            }
            if not set(body["entityIds"]) <= all_ids:
                raise AnalysisError("INVALID_INPUT", "发现对象不属于当前案件。")
            item = ReviewCheck.model_validate(
                check(
                    f"human:{uuid4()}",
                    body["nodeKey"],
                    "issue",
                    body["title"],
                    body["detail"],
                    body["factRefs"],
                    body["citationRefs"],
                    source="human",
                )
                | {k: body[k] for k in ("entityIds", "originalValues", "recommendation")}
            ).model_dump()
            commit_checks(task, [item])

        return await self.review_write(task_id, body, key, "manual_finding", update)

    async def add_review_record(self, task_id, kind, body, key):
        from .workspace_store import now, stable_id

        def update(task):
            state = task["reviewState"]
            if task["status"] == "completed" and kind not in {
                "reopen",
                "followup",
                "evidence_view",
            }:
                raise AnalysisError("REVIEW_CONFLICT", "请先重新打开人工复核。")
            validate_refs(task, body, viewed=kind == "human_completion")
            record = ReviewRecord.model_validate(
                {k: v for k, v in body.items() if k != "expectedRevision"}
                | dict(recordId=str(uuid4()), kind=kind, operatorId=actor(), at=now())
            ).model_dump()
            if body["previousRecordId"] and not any(
                r["recordId"] == body["previousRecordId"]
                and r["kind"] == kind
                and r["targetId"] == body["targetId"]
                for r in state["records"]
            ):
                raise AnalysisError("INVALID_INPUT", "前一记录不存在或不属于本事项。")
            plan = {p["checkId"]: p for p in state["checkPlan"]}
            findings = {f["findingId"]: f for f in state["findings"]}
            if kind == "evidence_view":
                if not validate_refs(task, body):
                    raise AnalysisError("INVALID_INPUT", "请选择要查看的具体依据。")
            elif kind == "human_completion":
                if body["state"] not in {"", "completed"}:
                    raise AnalysisError(
                        "INVALID_INPUT",
                        "人工补做完成记录不能表示未完成；仍需核实时请保存待补充核实决定。",
                    )
                record["state"] = "completed"
                if (
                    body["targetId"] not in plan
                    or not body["steps"].strip()
                    or not body["result"].strip()
                ):
                    raise AnalysisError("INVALID_INPUT", "请填写实际检查步骤、结果及检查项。")
                if plan[body["targetId"]]["nodeKey"] != body["nodeKey"]:
                    raise AnalysisError("INVALID_INPUT", "补做检查与节点不匹配。")
                if (
                    body["targetId"].startswith("gap:")
                    and not body["supplementIds"]
                    and not any(ref.startswith("business:") for ref in body["factRefs"])
                ):
                    raise AnalysisError(
                        "INVALID_INPUT",
                        "原档案缺失的资料须有补充材料或带来源的新业务记录，不能引用缺失声明冒充补齐。",
                    )
                if body["operation"]:
                    values = body["inputsFen"]
                    if not values or body["operation"] == "difference" and len(values) != 2:
                        raise AnalysisError("INVALID_INPUT", "请填写完整的计算输入。")
                    result = sum(values) if body["operation"] == "sum" else values[0] - values[1]
                    if result != body["resultFen"]:
                        raise AnalysisError("INVALID_INPUT", "人工计算结果与确定性计算不一致。")
                if (
                    body["nodeKey"] == "amount"
                    and not body["operation"]
                    and not any(
                        r["kind"] == "professional"
                        and r["targetId"] == body["targetId"]
                        and r["state"] == "opinion_received"
                        for r in state["records"]
                    )
                ):
                    raise AnalysisError(
                        "INVALID_INPUT", "金额补做须记录可计算输入，或关联专业核算意见。"
                    )
                if (
                    body["nodeKey"] == "clauses"
                    and not body["citationRefs"]
                    and not body["supplementIds"]
                ):
                    raise AnalysisError("INVALID_INPUT", "条款补做须有关联的条款原文。")
            elif kind == "scope_adjustment":
                ids = set(body["checkIds"])
                if not ids or not ids <= plan.keys() or body["state"] not in {"exclude", "restore"}:
                    raise AnalysisError("INVALID_INPUT", "请选择实际检查及调整方式。")
                if any(plan[check_id]["nodeKey"] != body["nodeKey"] for check_id in ids):
                    raise AnalysisError("INVALID_INPUT", "范围调整必须在对应检查节点记录。")
                if not body["result"].strip():
                    raise AnalysisError("INVALID_INPUT", "必须说明调整对结论的影响。")
                remaining = {
                    p["checkId"] for p in plan.values() if p["required"]
                } - excluded_checks(task)
                if body["state"] == "exclude" and not remaining - ids:
                    raise AnalysisError("INVALID_INPUT", "不能排除全部必要车损检查。")
                substantive = {
                    p["checkId"]
                    for p in plan.values()
                    if p["required"] and p["nodeKey"] in {"consistency", "clauses", "amount"}
                }
                if body["state"] == "exclude" and not substantive - excluded_checks(task) - ids:
                    raise AnalysisError("INVALID_INPUT", "不能只保留范围声明而排除全部实质检查。")
                # Shared accident/coverage facts cannot be hidden while dependent checks remain.
                shared = {
                    p["checkId"]
                    for p in plan.values()
                    if p["nodeKey"] in {"archive", "coverage"} and p["required"]
                }
                if body["state"] == "exclude" and ids & shared and remaining - ids:
                    raise AnalysisError(
                        "INVALID_INPUT", "保留项目依赖的范围和承保关键事实须先完成核实。"
                    )
            elif kind == "professional":
                if body["targetId"] not in findings and body["targetId"] not in plan:
                    raise AnalysisError("INVALID_INPUT", "专业事项不存在。")
                target = findings.get(body["targetId"]) or plan[body["targetId"]]
                if target["nodeKey"] != body["nodeKey"]:
                    raise AnalysisError("INVALID_INPUT", "专业事项与节点不匹配。")
                if not body["recipient"].strip() or body["state"] not in {
                    "registered",
                    "following",
                    "opinion_received",
                }:
                    raise AnalysisError("INVALID_INPUT", "请记录接收人/岗位和真实跟进状态。")
                if body["state"] == "opinion_received":
                    allowed = os.getenv("CASEPILOT_PROFESSIONAL_RECORDERS", "").split(",")
                    if actor() not in {v.strip() for v in allowed}:
                        raise AnalysisError("REVIEW_CONFLICT", "当前人员没有专业意见录入授权。")
                    if not body["source"].strip() or not body["result"].strip():
                        raise AnalysisError("INVALID_INPUT", "专业意见须有正文和来源。")
            elif kind == "followup":
                if (
                    body["targetId"] not in findings
                    or not body["recipient"].strip()
                    or body["state"] not in {"unhandled", "following", "completed"}
                ):
                    raise AnalysisError("INVALID_INPUT", "请填写对应发现、责任去向和办理状态。")
                if not body["source"].strip():
                    raise AnalysisError("INVALID_INPUT", "办理状态必须说明记录来源。")
                if findings[body["targetId"]]["nodeKey"] != body["nodeKey"]:
                    raise AnalysisError("INVALID_INPUT", "办理记录必须关联实际发现节点。")
            elif kind == "business_record":
                if not body["source"].strip() or not body["result"].strip():
                    raise AnalysisError("INVALID_INPUT", "业务记录须有明确来源和原始内容。")
                task["facts"].append(
                    dict(
                        factId=f"business:{record['recordId']}",
                        fieldPath=f"businessRecords[{record['recordId']}]",
                        value=dict(
                            content=body["result"],
                            source=body["source"],
                            at=record["at"],
                            operatorId=actor(),
                        ),
                        sourceType="business",
                        materialId=None,
                    )
                )
            elif kind == "reopen":
                if task["status"] != "completed":
                    raise AnalysisError("REVIEW_CONFLICT", "只有已最终完成的任务需要重新打开。")
                if self.active_task(task["conversationId"]):
                    raise AnalysisError("REVIEW_CONFLICT", "同会话已有活动任务，请先处理。")
                state["reviewCycleId"] += 1
                task.pop("_review", None)
                task["status"] = "waiting_review"
                task["pendingReview"] = dict(
                    interruptKey=stable_id(task["id"], f"review:{state['reviewCycleId']}"),
                    checkpointId="manual",
                    revision=task["revision"],
                    reason=body["comment"],
                )
            state["records"].append(record)
            if (
                kind == "followup"
                and task["status"] == "completed"
                and not eligibility(task)["allowed"]
            ):
                raise AnalysisError("REVIEW_CONFLICT", "出现实质性变化，请重新打开复核。")

        return await self.review_write(task_id, body, key, kind, update)

    async def start_business_node(self, task_id, node_key):
        from .workspace_store import now

        def update(task):
            node = next(n for n in task["reviewState"]["businessNodes"] if n["nodeKey"] == node_key)
            if node["status"] == "completed" and node_key != "report":
                return
            if node["status"] in {"failed", "unable", "running", "completed"}:
                task["reviewState"]["nodeHistory"].append(deepcopy(node))
                node["attempt"] += 1
                node["nodeRunId"] = f"{task_id}:{node_key}:{node['attempt']}"
            node.update(
                status="running",
                startedAt=now(),
                endedAt=None,
                durationMs=0,
                summary="正在执行实际检查",
                reason="",
            )
            self.append(task, "business_node.started", node, f"business:{node['nodeRunId']}:start")

        return await self.edit(task_id, update)

    async def finish_business_node(self, task_id, node_key, *, error="", unable=False):

        from .workspace_store import now

        def update(task):
            node = next(n for n in task["reviewState"]["businessNodes"] if n["nodeKey"] == node_key)
            if node["status"] == "completed":
                return
            rows = [c for c in task["checks"] if c["nodeKey"] == node_key]
            status = (
                "unable"
                if unable
                else "failed"
                if error
                else "unable"
                if any(c["status"] == "limited" for c in rows)
                else "not_applicable"
                if rows and all(c["status"] == "not_applicable" for c in rows)
                else "completed"
            )
            at = now()
            node.update(
                status=status,
                endedAt=at,
                durationMs=sum(
                    call["durationMs"]
                    for call in task["execution"]["tools"]
                    if call["parentNodeRunId"] == node["nodeRunId"] and call["status"] != "running"
                ),
                summary=f"保存 {len(rows)} 项检查，{sum(c['status'] == 'limited' for c in rows)} 项受限",
                reason=error or "；".join(c["title"] for c in rows if c["status"] == "limited"),
            )
            self.append(
                task, f"business_node.{status}", node, f"business:{node['nodeRunId']}:{status}"
            )
            self.review_changed(task)

        return await self.edit(task_id, update)

    async def publish_checks(self, task_id, checks, *, facts=None, citations=None):
        def update(task):
            original = deepcopy(task["reviewState"])
            changed = (
                facts is not None
                and facts != task["facts"]
                or citations is not None
                and citations != task["citations"]
            )
            if facts is not None:
                business = [f for f in task["facts"] if f["sourceType"] == "business"]
                task["facts"] = list(
                    {f["factId"]: deepcopy(f) for f in [*facts, *business]}.values()
                )
            if citations is not None:
                task["citations"] = deepcopy(citations)
            commit_checks(task, checks)
            if changed or task["reviewState"] != original:
                self.review_changed(task)

        return await self.edit(task_id, update)

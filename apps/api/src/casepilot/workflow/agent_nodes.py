"""Bounded model decisions, actual tool execution and checked structured results."""

import json

from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import ValidationError

from ..analyses.agent_errors import AgentError
from ..analyses.checks import assessment_checks, material_scope_checks, merge_checks, run_checks
from ..analyses.evidence import Assessment, case_facts, checked_assessment, merge_citations
from ..knowledge.errors import KnowledgeError, KnowledgeOperationError
from ..model.chat import assistant_message
from ..model.errors import ModelError
from .prompts import ASSESSMENT_POLICY, PROMPT_VERSION, TOOL_POLICY
from .tools import SearchInput, build_analysis_tools


def normalized_query(query):
    return " ".join(query.split()).casefold()


class AgentNodes:
    def __init__(self, context, ledger, knowledge, chat):
        self.context, self.ledger, self.chat = context, ledger, chat
        self.tools = build_analysis_tools(context, knowledge)
        self.failed_nodes = set()

    def stage(self, key, operation, *, finish=False):
        async def execute(state):
            if key in self.failed_nodes:
                return {}
            self.ledger.node_key = key
            store, task_id = self.ledger.store, self.ledger.task_id
            current = next(
                n for n in store.get(task_id)["reviewState"]["businessNodes"] if n["nodeKey"] == key
            )
            if current["status"] not in {"running", "completed"}:
                await store.start_business_node(task_id, key)
            self.ledger.node_run_id = next(
                n["nodeRunId"]
                for n in store.get(task_id)["reviewState"]["businessNodes"]
                if n["nodeKey"] == key
            )
            try:
                result = await operation(state)
                if finish and current["status"] != "completed":
                    await store.finish_business_node(task_id, key)
                return result
            except (AgentError, ModelError, KnowledgeError, KnowledgeOperationError) as exc:
                self.failed_nodes.add(key)
                from ..analyses.checks import check

                row = check(
                    f"{key}:assessment"
                    if key in {"consistency", "clauses", "amount"}
                    else f"{key}:execution",
                    key,
                    "limited",
                    "实际检查中断",
                    f"{exc.code}，需显式恢复或人工补做。",
                )
                await store.publish_checks(
                    task_id,
                    [row],
                    facts=state.get("facts") or case_facts(self.context["caseSnapshot"]),
                )
                await store.finish_business_node(
                    task_id,
                    key,
                    error=exc.code,
                    unable=isinstance(exc, KnowledgeError)
                    or exc.code in {"PINNED_MATERIAL_UNAVAILABLE", "MATERIAL_TEXT_UNAVAILABLE"},
                )
                return {
                    "checks": [*state.get("checks", []), row],
                    "facts": state.get("facts") or case_facts(self.context["caseSnapshot"]),
                    "citations": state.get("citations", []),
                    "pendingTool": None,
                    "stopReason": "execution_failed",
                    "decisions": state.get("decisions", 0),
                    "queries": state.get("queries", []),
                    "supplements": state.get("supplements", 0),
                }

        return execute

    async def query(self, state):
        result = await self.ledger.run(
            "tool:query_case", "local", lambda: self.tools["query_case"].ainvoke({})
        )
        await self.ledger.store.publish_checks(self.ledger.task_id, [], facts=result["facts"])
        return {"facts": result["facts"]}

    async def validate(self, state):
        result = await self.ledger.run(
            "tool:validate_materials", "local", lambda: self.tools["validate_materials"].ainvoke({})
        )
        return {"ruleFindings": result}

    async def checks(self, state, node):
        async def execute():
            return run_checks(self.context["caseSnapshot"], node)

        rows = await self.ledger.run(f"check:{node}", "local", execute)
        if node == "consistency" and not any(
            key.startswith("tool:query_case:") and call["status"] == "completed"
            for key, call in self.ledger.store.get(self.ledger.task_id)["_agent"]["calls"].items()
        ):
            for row in rows:
                if row["checkId"] == "material_provenance":
                    row.update(status="limited", detail="材料读取未完成，不能确认固定正文及版本。")
        await self.ledger.store.publish_checks(self.ledger.task_id, rows)
        return {"checks": [*state.get("checks", []), *rows]}

    async def archive(self, state):
        result = await self.checks(state, "archive")
        rows = material_scope_checks(state["facts"])
        await self.ledger.store.publish_checks(self.ledger.task_id, rows)
        return {"checks": [*result["checks"], *rows]}

    async def coverage(self, state):
        return await self.checks(state, "coverage")

    async def consistency(self, state):
        return await self.checks(state, "consistency")

    async def amount(self, state):
        return await self.assess(state, phase="amount")

    async def amount_rules(self, state):
        return await self.checks(state, "amount")

    async def material_assessment(self, state):
        if not any(
            f["sourceType"] == "material" and isinstance(f["value"], str) and f["value"].strip()
            for f in state["facts"]
        ):
            raise AgentError("MATERIAL_TEXT_UNAVAILABLE")
        return await self.assess(state, phase="consistency")

    async def retrieve(self, state):
        case = self.context["caseSnapshot"]["payload"]
        targets = set(case["reviewScope"]["targetClaimIds"])
        coverage_ids = {
            a["coverageId"] for a in case.get("approvals", []) if a["claimId"] in targets
        }
        names = {
            "CTPL": "机动车交通事故责任强制保险",
            "OWN_DAMAGE": "机动车损失保险",
            "THIRD_PARTY": "机动车第三者责任保险",
        }
        active = sorted(
            {
                names.get(c["coverageCode"], c["coverageCode"])
                for p in case.get("policies", [])
                for c in p.get("coverages", [])
                if c["coverageId"] in coverage_ids
            }
        )
        query = (
            self.context["question"]
            + " "
            + " ".join(active)
            + " 保险责任 赔偿处理 部分损失计算 免赔 "
            + " ".join(f["title"] for f in state["ruleFindings"])
        )[:2000]
        rows = await self.ledger.run(
            "retrieval:initial",
            "retrieval",
            lambda: self.tools["search_clauses"].ainvoke({"query": query}),
        )
        return {
            "citations": merge_citations([], rows, self.context),
            "queries": [normalized_query(query), normalized_query(self.context["question"])],
            "decisions": 0,
            "supplements": 0,
            "stopReason": None,
            "pendingTool": None,
        }

    def evidence(self, state):
        facts = []
        for fact in state["facts"]:
            value = fact["value"]
            if fact["factId"].startswith("documents:") and isinstance(value, dict):
                value = {
                    key: value[key]
                    for key in (
                        "documentId",
                        "title",
                        "materialType",
                        "status",
                        "version",
                        "entityIds",
                    )
                    if key in value
                }
            facts.append({"factId": fact["factId"], "value": value})
        return {
            "history": self.context.get("history", []),
            "question": self.context["question"],
            "facts": facts,
            "ruleFindings": state["ruleFindings"],
            "completedChecks": [
                {k: row[k] for k in ("checkId", "nodeKey", "status", "title", "factRefs")}
                for row in state.get("checks", [])
            ],
            "scopeItems": self.context["caseSnapshot"].get("scopeItems", []),
            "knowledgeBindings": [
                {k: binding[k] for k in ("documentId", "version", "sectionIds", "status")}
                for binding in self.context["knowledgeBindings"]
            ],
            "citations": [
                {
                    k: row[k]
                    for k in (
                        "citationId",
                        "productCode",
                        "clauseVersion",
                        "fileName",
                        "page",
                        "content",
                    )
                }
                for row in state["citations"]
            ],
        }

    async def decide(self, state):
        if state.get("stopReason") == "execution_failed":
            return {"pendingTool": None}
        messages = state.get("messages") or [
            {"role": "system", "content": TOOL_POLICY},
            {
                "role": "user",
                "content": json.dumps(
                    self.evidence(state), ensure_ascii=False, separators=(",", ":")
                ),
            },
        ]
        turn = await self.ledger.run(
            f"model:decision:{state['decisions']}",
            "model",
            lambda: self.chat.complete(
                messages, tools=[convert_to_openai_tool(self.tools["search_clauses"])]
            ),
            reserve_model=3,
        )
        calls = turn["toolCalls"]
        update = {"decisions": state["decisions"] + 1, "pendingTool": None, "messages": messages}
        if not calls:
            return update
        if len(calls) != 1 or calls[0]["name"] != "search_clauses":
            raise AgentError("MODEL_TOOL_NOT_ALLOWED")
        try:
            args = SearchInput.model_validate(calls[0]["arguments"])
        except ValidationError:
            raise AgentError("MODEL_TOOL_ARGUMENT_INVALID") from None
        query = args.query.strip()
        if not query:
            raise AgentError("MODEL_TOOL_ARGUMENT_INVALID")
        if normalized_query(query) in state["queries"]:
            return update | {"stopReason": "duplicate_query"}
        if state["supplements"] >= 2:
            return update | {"stopReason": "retrieval_budget_exhausted"}
        call = calls[0] | {"arguments": {"query": query}}
        assistant = assistant_message(turn)
        return update | {"pendingTool": call, "messages": [*messages, assistant]}

    async def supplement(self, state):
        call = state["pendingTool"]
        rows = await self.ledger.run(
            f"retrieval:supplement:{state['supplements']}",
            "retrieval",
            lambda: self.tools["search_clauses"].ainvoke(call["arguments"]),
        )
        citations = merge_citations(state["citations"], rows, self.context)
        added = len(citations) > len(state["citations"])
        return {
            "citations": citations,
            "queries": [*state["queries"], normalized_query(call["arguments"]["query"])],
            "supplements": state["supplements"] + 1,
            "pendingTool": None,
            "stopReason": None if added else "no_new_evidence",
            "messages": [
                *state["messages"],
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(rows, ensure_ascii=False),
                },
            ],
        }

    async def assess(self, state, phase="clauses"):
        if phase == "clauses" and state.get("stopReason") == "execution_failed":
            return {}
        messages = [
            {
                "role": "system",
                "content": ASSESSMENT_POLICY
                + f"\n本次仅执行 nodeKey={phase}。checkedItems 只输出本节点实际检查；不代替其他节点。"
                + "\n"
                + json.dumps(Assessment.model_json_schema(), ensure_ascii=False),
            },
            {
                "role": "user",
                "content": json.dumps(
                    self.evidence(state) | {"phase": phase},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            },
        ]
        turn = await self.ledger.run(
            f"model:assessment:{phase}",
            "model",
            lambda: self.chat.complete(messages, json_mode=True),
            reserve_model={"consistency": 3, "clauses": 2, "amount": 1}[phase],
        )

        quote_errors = []

        def check(reply):
            quote_errors.clear()
            if reply["toolCalls"]:
                raise AgentError("MODEL_TOOL_NOT_ALLOWED")
            result = checked_assessment(
                json.loads(reply["content"]), state["facts"], state["citations"]
            )
            for row in [*result["findings"], *result["checkedItems"]]:
                if (
                    phase == "clauses"
                    and "缺少可定位且支持本项表述的条款原文摘录" in row["pendingItems"]
                ):
                    quote = "".join(row["supportQuote"].split())
                    quote_errors.append(
                        dict(
                            title=row["title"],
                            citationRefs=row["citationRefs"],
                            matchingCitationIds=[
                                c["citationId"]
                                for c in state["citations"]
                                if quote and quote in "".join(c["content"].split())
                            ],
                        )
                    )
            if quote_errors:
                raise AgentError("ANALYSIS_QUOTE_INVALID")
            return result

        try:
            assessment = check(turn)
        except (ValidationError, ValueError, AgentError) as error:
            diagnostic = (
                json.dumps(
                    error.errors(include_input=False, include_context=False), ensure_ascii=False
                )[:1500]
                if isinstance(error, ValidationError)
                else getattr(error, "code", "INVALID_JSON")
            )
            if quote_errors:
                diagnostic += " " + json.dumps(quote_errors, ensure_ascii=False)[:2000]
            repaired = await self.ledger.run(
                f"model:assessment:{phase}:repair",
                "model",
                lambda: self.chat.complete(
                    [
                        *messages,
                        assistant_message(turn),
                        {
                            "role": "user",
                            "content": f"前次输出校验失败：{diagnostic}。只修复本节点的结构和引用。factRefs 只放案件/材料事实 ID；citationRefs 只放检索条款 ID，不能放 EV 或 evidence: 材料编号。条款 supportQuote 必须连续逐字摘录所引用条款，不能填写保单或核赔材料原文；其他节点不需要条款时写空字符串。不额外生成引用合法性检查；不能支持的实质判断标为 insufficient、limitation，不添加新来源。",
                        },
                    ],
                    json_mode=True,
                ),
                repair=True,
                reserve_model=0,
            )
            try:
                assessment = check(repaired)
            except (ValidationError, ValueError, AgentError):
                raise AgentError("ANALYSIS_OUTPUT_INVALID") from None
        if state.get("stopReason") == "retrieval_budget_exhausted":
            assessment["insufficientEvidence"] = True
        assessment["findings"] = [r for r in assessment["findings"] if r["nodeKey"] == phase]
        assessment["checkedItems"] = [
            r for r in assessment["checkedItems"] if r["nodeKey"] == phase
        ]
        rows = [
            r
            for r in assessment_checks(
                assessment, self.context["caseSnapshot"], state.get("citations", [])
            )
            if r["nodeKey"] == phase
        ]
        completed = assessment["checkedItems"]
        from ..analyses.checks import check

        rows.append(
            check(
                f"{phase}:assessment",
                phase,
                "passed"
                if completed
                and not assessment["insufficientEvidence"]
                and all(
                    r["evidenceStatus"] == "supported" and r["category"] != "limitation"
                    for r in completed
                )
                else "limited",
                {
                    "consistency": "材料原文一致性",
                    "clauses": "条款与原处理依据",
                    "amount": "金额口径及支付解释核对",
                }[phase],
                assessment["summary"],
                [ref for r in completed for ref in r["factRefs"]],
                [ref for r in completed for ref in r["citationRefs"]],
                "ai",
            )
        )
        checks = merge_checks(
            state.get("checks", []),
            rows,
            assessment,
        )
        await self.ledger.store.publish_checks(
            self.ledger.task_id, checks, citations=state.get("citations", [])
        )
        result = {
            "context": self.context,
            "facts": state["facts"],
            "ruleFindings": state["ruleFindings"],
            "modelAnalysis": assessment,
            "citations": state["citations"],
            "checks": checks,
            "needsReview": True,
            "stopReason": state.get("stopReason"),
            "promptVersion": PROMPT_VERSION,
        }
        previous = state.get("assessment", {})
        combined = assessment | dict(
            findings=[*previous.get("findings", []), *assessment["findings"]],
            checkedItems=[*previous.get("checkedItems", []), *assessment["checkedItems"]],
            insufficientEvidence=previous.get("insufficientEvidence", False)
            or assessment["insufficientEvidence"],
        )
        return {"assessment": combined, "result": result, "checks": checks}

    async def finish(self, state):
        task = self.ledger.store.get(self.ledger.task_id)
        return {
            "result": dict(
                context=self.context,
                needsReview=True,
                stopReason=state.get("stopReason"),
                promptVersion=PROMPT_VERSION,
                facts=task["facts"],
                ruleFindings=state.get("ruleFindings", []),
                modelAnalysis=state.get("assessment", dict(findings=[], insufficientEvidence=True)),
                citations=task["citations"],
                checks=task["checks"],
            )
        }

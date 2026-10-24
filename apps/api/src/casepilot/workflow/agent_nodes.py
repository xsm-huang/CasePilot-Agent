"""Bounded model decisions, actual tool execution and checked structured results."""

import json

from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import ValidationError

from ..analyses.agent_errors import AgentError
from ..analyses.evidence import Assessment, checked_assessment, merge_citations
from .prompts import ASSESSMENT_POLICY, PROMPT_VERSION, TOOL_POLICY
from .tools import SearchInput, build_analysis_tools


def normalized_query(query):
    return " ".join(query.split()).casefold()


class AgentNodes:
    def __init__(self, context, ledger, knowledge, chat):
        self.context, self.ledger, self.chat = context, ledger, chat
        self.tools = build_analysis_tools(context, knowledge)

    async def query(self, state):
        result = await self.ledger.run(
            "tool:query_case", "local", lambda: self.tools["query_case"].ainvoke({})
        )
        return {"facts": result["facts"]}

    async def validate(self, state):
        result = await self.ledger.run(
            "tool:validate_materials", "local", lambda: self.tools["validate_materials"].ainvoke({})
        )
        return {"ruleFindings": result}

    async def retrieve(self, state):
        query = (
            self.context["question"] + " " + " ".join(f["title"] for f in state["ruleFindings"])
        )[:2000]
        rows = await self.ledger.run(
            "retrieval:initial",
            "retrieval",
            lambda: self.tools["search_clauses"].ainvoke({"query": query}),
        )
        return {
            "citations": merge_citations([], rows, self.context),
            "queries": [normalized_query(query)],
            "decisions": 0,
            "supplements": 0,
            "stopReason": None,
            "pendingTool": None,
        }

    def evidence(self, state):
        return {
            "question": self.context["question"],
            "facts": state["facts"],
            "ruleFindings": state["ruleFindings"],
            "citations": state["citations"],
        }

    async def decide(self, state):
        messages = state.get("messages") or [
            {"role": "system", "content": TOOL_POLICY},
            {"role": "user", "content": json.dumps(self.evidence(state), ensure_ascii=False)},
        ]
        turn = await self.ledger.run(
            f"model:decision:{state['decisions']}",
            "model",
            lambda: self.chat.complete(
                messages, tools=[convert_to_openai_tool(self.tools["search_clauses"])]
            ),
            reserve_model=4,
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
        assistant = {
            "role": "assistant",
            "content": turn["content"] or None,
            "tool_calls": [
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": json.dumps(call["arguments"], ensure_ascii=False),
                    },
                }
            ],
        }
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

    async def assess(self, state):
        messages = [
            {
                "role": "system",
                "content": ASSESSMENT_POLICY
                + "\n"
                + json.dumps(Assessment.model_json_schema(), ensure_ascii=False),
            },
            {"role": "user", "content": json.dumps(self.evidence(state), ensure_ascii=False)},
        ]
        turn = await self.ledger.run(
            "model:assessment", "model", lambda: self.chat.complete(messages, json_mode=True)
        )

        def check(reply):
            if reply["toolCalls"]:
                raise AgentError("MODEL_TOOL_NOT_ALLOWED")
            return checked_assessment(
                json.loads(reply["content"]), state["facts"], state["citations"]
            )

        try:
            assessment = check(turn)
        except (ValidationError, ValueError, AgentError):
            repaired = await self.ledger.run(
                "model:assessment:repair",
                "model",
                lambda: self.chat.complete(
                    [
                        *messages,
                        {"role": "assistant", "content": turn["content"]},
                        {
                            "role": "user",
                            "content": "前次 JSON 结构或引用未通过校验。只修复结构及允许的事实/引用 ID；无法支持的结论标为 insufficient，不添加新来源。",
                        },
                    ],
                    json_mode=True,
                ),
                repair=True,
            )
            try:
                assessment = check(repaired)
            except (ValidationError, ValueError, AgentError):
                raise AgentError("ANALYSIS_OUTPUT_INVALID") from None
        if state.get("stopReason"):
            assessment["insufficientEvidence"] = True
        result = {
            "context": self.context,
            "facts": state["facts"],
            "ruleFindings": state["ruleFindings"],
            "modelAnalysis": assessment,
            "citations": state["citations"],
            "needsReview": bool(
                state["ruleFindings"]
                or assessment["findings"]
                or assessment["insufficientEvidence"]
            ),
            "stopReason": state.get("stopReason"),
            "promptVersion": PROMPT_VERSION,
        }
        return {"assessment": assessment, "result": result}

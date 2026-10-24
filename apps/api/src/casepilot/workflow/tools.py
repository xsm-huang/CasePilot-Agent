"""Real LangChain tools with immutable server-side case and knowledge scope."""

from copy import deepcopy

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field

from ..analyses.evidence import case_facts
from ..cases.evidence_rules import evaluate_evidence_rules


class EmptyToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SearchInput(EmptyToolInput):
    query: str = Field(min_length=1, max_length=2000)


class ScopedTool(StructuredTool):
    def _to_args_and_kwargs(self, tool_input, tool_call_id):
        # LangChain skips validation for zero-field schemas; still reject extra scope inputs.
        self.args_schema.model_validate(tool_input)
        return super()._to_args_and_kwargs(tool_input, tool_call_id)


def build_analysis_tools(context, knowledge):
    pinned = deepcopy(context)
    claim = pinned["caseSnapshot"]

    async def query_case():
        return {"caseSnapshot": deepcopy(claim), "facts": case_facts(claim)}

    async def validate_materials():
        return evaluate_evidence_rules(claim, case_facts(claim))

    async def search_clauses(query: str):
        return await knowledge.search(
            pinned["productCode"],
            pinned["clauseVersion"],
            pinned["generationId"],
            query.strip(),
            limit=4,
            profile=pinned["embeddingProfile"],
        )

    return {
        "query_case": ScopedTool.from_function(
            coroutine=query_case,
            name="query_case",
            description="读取当前任务固定的案件事实及来源。",
            args_schema=EmptyToolInput,
        ),
        "validate_materials": ScopedTool.from_function(
            coroutine=validate_materials,
            name="validate_materials",
            description="确定性检查材料、日期有效性与跨来源冲突，返回原始事实引用。",
            args_schema=EmptyToolInput,
        ),
        "search_clauses": ScopedTool.from_function(
            coroutine=search_clauses,
            name="search_clauses",
            description="在当前任务固定的险种、版本和 generation 中补充检索条款。仅提供需要核查的问题。",
            args_schema=SearchInput,
        ),
    }

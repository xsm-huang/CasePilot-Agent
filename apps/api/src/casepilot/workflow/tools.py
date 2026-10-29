"""Real LangChain tools with immutable server-side case and knowledge scope."""

import asyncio
import hashlib
from copy import deepcopy

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field

from ..analyses.agent_errors import AgentError
from ..analyses.evidence import case_facts
from ..cases.evidence_rules import evaluate_evidence_rules
from ..cases.review_repository import review_document
from ..knowledge.pdf import parse_pages
from ..schemas.agent import Fact


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
        facts = case_facts(claim)
        for document in claim["payload"].get("documents", []):
            if document["status"] != "available":
                continue
            resolved = review_document(claim["caseId"], document["documentId"])
            if not resolved:
                raise AgentError("PINNED_MATERIAL_UNAVAILABLE")
            content = resolved[0].read_bytes()
            if hashlib.sha256(content).hexdigest() != document["sha256"]:
                raise AgentError("PINNED_MATERIAL_CHANGED")
            for page, text in await asyncio.to_thread(parse_pages, content):
                facts.append(
                    Fact(
                        factId=f"material_pages:{document['documentId']}:{page}",
                        fieldPath=f"documents[{document['documentId']}].pages[{page}]",
                        value=text,
                        sourceType="material",
                        materialId=document["documentId"],
                    ).model_dump()
                )
        return {"caseSnapshot": deepcopy(claim), "facts": facts}

    async def validate_materials():
        return evaluate_evidence_rules(claim, case_facts(claim))

    async def search_clauses(query: str):
        rows = []
        bindings = [item for item in pinned["knowledgeBindings"] if item["status"] == "ready"]
        for binding in bindings:
            rows.extend(
                await knowledge.search(
                    binding["productCode"],
                    binding["clauseVersion"],
                    binding["generationId"],
                    query.strip(),
                    limit=4,
                    profile=binding["embeddingProfile"],
                )
            )
        return sorted(rows, key=lambda item: item.get("distance", 1))[:12]

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
            description="在当前任务固定的知识版本中补充检索条款。仅提供需要核查的问题。",
            args_schema=SearchInput,
        ),
    }

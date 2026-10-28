"""Actual LangGraph and LangChain tools, using deterministic external adapters."""

import pytest
from agent_fixtures import (
    FakeKnowledge,
    RecordingRepository,
    ScriptedChat,
    assessment,
    clause,
    tool_turn,
)
from casepilot.analyses.agent import run_agent_analysis
from casepilot.analyses.agent_errors import AgentError
from casepilot.analyses.store import Store
from casepilot.cases.review_repository import get_review_case_input, review_scope_items
from casepilot.knowledge.config import PROFILE
from casepilot.model.config import read_model_config
from casepilot.workflow.prompts import PROMPT_VERSION
from casepilot.workflow.tools import build_analysis_tools
from pydantic import ValidationError

DEFAULT_QUESTION = "请核查案件事实、材料完整性及条款依据。"


async def prepared(question=DEFAULT_QUESTION):
    store = Store()
    task = await store.create("C02")
    store.repository = RecordingRepository()
    case = get_review_case_input("C02")
    snapshot = {
        "snapshotKind": "closed_claim_review",
        "caseId": "C02",
        "caseRevision": case["caseRevision"],
        "preparedAt": case["preparedAt"],
        "payload": case,
        "scopeItems": review_scope_items(case),
        "knowledgeBindings": [{
            **case["knowledgeRefs"][0], "status": "ready", "generationId": "generation-1",
            "productCode": "AUTO-COMPREHENSIVE", "clauseVersion": "2025-01",
            "embeddingProfile": PROFILE,
        }],
    }
    store.tasks[task["id"]]["_agent"] = {
        "context": {
            "caseId": "C02", "caseSnapshot": snapshot, "inputVersion": "test-input",
            "knowledgeBindings": snapshot["knowledgeBindings"],
            "modelProfile": read_model_config({"ZHIPU_API_KEY": "test-no-network"}).chat_model,
            "promptVersion": PROMPT_VERSION, "question": question,
        },
        "calls": {}, "counts": {"model": 0, "retrieval": 0, "repair": 0},
    }
    return store, task["id"]


async def test_agent_entry_rejects_ephemeral_storage_before_any_external_request():
    store = Store()
    task = await store.create("C02")
    knowledge, chat = FakeKnowledge(), ScriptedChat()
    with pytest.raises(AgentError, match="PERSISTENT_STORAGE_REQUIRED"):
        await run_agent_analysis(store, task["id"], knowledge, chat)
    assert not chat.calls and not knowledge.calls


async def test_real_tools_and_structured_model_analysis_use_pinned_knowledge():
    store, task_id = await prepared()
    knowledge, chat = FakeKnowledge(), ScriptedChat()
    result = await run_agent_analysis(store, task_id, knowledge, chat)
    assert result["ruleFindings"] == []
    assert result["citations"][0]["page"] == 1
    assert result["modelAnalysis"]["findings"][0]["citationRefs"] == ["chunk-1"]
    assert len(chat.calls) == 2
    assert chat.calls[0]["tools"][0]["function"]["name"] == "search_clauses"
    assert chat.calls[1]["json"] is True
    assert knowledge.calls[0][0:3] == ("AUTO-COMPREHENSIVE", "2025-01", "generation-1")
    before = len(chat.calls), len(knowledge.calls)
    knowledge.active = "generation-2"
    assert await run_agent_analysis(store, task_id, knowledge, chat) == result
    assert (len(chat.calls), len(knowledge.calls)) == before
    assert "_agent" not in store.public(store.get(task_id))


async def test_actual_tool_call_protocol_performs_supplement_then_returns_result():
    store, task_id = await prepared()
    knowledge = FakeKnowledge([[clause()], [clause(2)]])
    reasoning = "private reasoning retained exactly\nfor tool continuation"
    chat = ScriptedChat([tool_turn("请补充维修费用凭证条款") | {"_reasoningContent": reasoning}])
    result = await run_agent_analysis(store, task_id, knowledge, chat)
    assert len(knowledge.calls) == 2
    assert len(result["citations"]) == 2
    messages = chat.calls[1]["messages"]
    assert messages[-2]["role"] == "assistant"
    assert messages[-2]["reasoning_content"] == reasoning
    assert messages[-1]["role"] == "tool"
    assert messages[-1]["tool_call_id"] == messages[-2]["tool_calls"][0]["id"]
    assert reasoning not in str(result)
    assert reasoning not in str(store.public(store.get(task_id)))


async def test_supplement_limit_is_enforced_even_when_model_keeps_requesting():
    store, task_id = await prepared()
    knowledge = FakeKnowledge([[clause()], [clause(2)], [clause(3)]])
    chat = ScriptedChat(
        [
            tool_turn("first supplement"),
            tool_turn("second supplement"),
            tool_turn("third supplement"),
        ]
    )
    result = await run_agent_analysis(store, task_id, knowledge, chat)
    assert len(knowledge.calls) == 3
    assert result["stopReason"] == "retrieval_budget_exhausted"
    assert result["modelAnalysis"]["insufficientEvidence"] is True
    assert result["needsReview"] is True
    assert store.get(task_id)["_agent"]["counts"]["model"] == 4


@pytest.mark.parametrize("mode", ["duplicate", "no-new"])
async def test_repeated_queries_or_no_new_evidence_stop_the_loop(mode):
    question = "current question"
    store, task_id = await prepared(question)
    query = question if mode == "duplicate" else "different query"
    result = await run_agent_analysis(
        store, task_id, FakeKnowledge(), ScriptedChat([tool_turn(query)]), question=question
    )
    assert result["stopReason"] == ("duplicate_query" if mode == "duplicate" else "no_new_evidence")
    assert result["needsReview"] is True


@pytest.mark.parametrize(
    "turn", [tool_turn("query", productCode="OTHER"), tool_turn("query", name="delete_document")]
)
async def test_model_cannot_change_scope_or_select_unknown_tools(turn):
    store, task_id = await prepared()
    knowledge = FakeKnowledge()
    with pytest.raises(AgentError):
        await run_agent_analysis(store, task_id, knowledge, ScriptedChat([turn]))
    assert len(knowledge.calls) == 1


async def test_invalid_reference_is_repaired_once_and_invalid_second_output_fails():
    store, task_id = await prepared()
    chat = ScriptedChat(assessments=[assessment(citation="other-task-chunk"), assessment()])
    result = await run_agent_analysis(store, task_id, FakeKnowledge(), chat)
    assert result["modelAnalysis"]["findings"][0]["citationRefs"] == ["chunk-1"]
    assert store.get(task_id)["_agent"]["counts"]["repair"] == 1
    other, other_id = await prepared()
    chat = ScriptedChat(assessments=["not JSON", assessment(fact="invented")])
    with pytest.raises(AgentError, match="ANALYSIS_OUTPUT_INVALID"):
        await run_agent_analysis(other, other_id, FakeKnowledge(), chat)
    assert len(chat.calls) == 3


async def test_tools_bind_no_scope_inputs():
    store, task_id = await prepared()
    knowledge, chat = FakeKnowledge(), ScriptedChat()
    result = await run_agent_analysis(store, task_id, knowledge, chat)
    tools = build_analysis_tools(result["context"], knowledge)
    with pytest.raises(ValidationError):
        await tools["query_case"].ainvoke({"caseId": "another"})
    with pytest.raises(ValidationError):
        await tools["search_clauses"].ainvoke({"query": "evidence", "generationId": "another"})

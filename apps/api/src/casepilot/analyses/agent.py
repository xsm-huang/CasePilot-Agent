"""Bounded analysis component used by the durable workspace graph."""

from ..workflow.agent_graph import create_agent_graph
from ..workflow.prompts import PROMPT_VERSION
from .agent_errors import AgentError
from .ledger import TaskLedger


async def run_agent_analysis(
    store,
    task_id,
    knowledge,
    chat,
    *,
    question="请核查案件事实、材料完整性及条款依据。",
):
    if store.repository is None:
        raise AgentError("PERSISTENT_STORAGE_REQUIRED")
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000:
        raise AgentError("INVALID_QUESTION")
    question = question.strip()
    task = store.get(task_id)
    saved = task.get("_agent", {}).get("context")
    if saved:
        context = saved
        if (
            context["question"] != question
            or context["caseId"] != task["caseId"]
            or context["modelProfile"] != chat.config.chat_model
            or context["promptVersion"] != PROMPT_VERSION
        ):
            raise AgentError("AGENT_CONTEXT_CONFLICT")
    else:
        raise AgentError("AGENT_CONTEXT_MISSING")
    ledger = TaskLedger(store, task_id)
    await ledger.initialize(context)
    graph = create_agent_graph(context, ledger, knowledge, chat)
    state = await graph.ainvoke({}, {"recursion_limit": 20})
    return state["result"]

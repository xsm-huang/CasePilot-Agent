"""Call accounting is reserved before effects, bounded and not reset on recovery."""

import asyncio

import pytest
from casepilot.analyses.agent_errors import AgentError
from casepilot.analyses.ledger import TaskLedger
from casepilot.analyses.store import Store
from casepilot.model.errors import ModelError


async def prepared():
    store = Store()
    task = await store.create("C02")
    ledger = TaskLedger(store, task["id"])
    await ledger.initialize({"generationId": "pinned"})
    return store, task["id"], ledger


async def success():
    return {"result": "verified"}


async def test_completed_effects_are_reused_and_context_cannot_be_replaced():
    store, task_id, ledger = await prepared()
    assert await ledger.run("model", "model", success) == {"result": "verified"}
    resumed = TaskLedger(store, task_id)
    await resumed.initialize({"generationId": "pinned"})

    async def forbidden():
        pytest.fail("A committed effect must not be called again")

    assert await resumed.run("model", "model", forbidden) == {"result": "verified"}
    assert store.get(task_id)["_agent"]["counts"]["model"] == 1
    with pytest.raises(AgentError, match="AGENT_CONTEXT_CONFLICT"):
        await resumed.initialize({"generationId": "new"})


async def test_global_budget_preserves_three_report_calls_and_retrieval_limit():
    store, task_id, ledger = await prepared()
    for index in range(5):
        await ledger.run(f"analysis-{index}", "model", success)
    with pytest.raises(AgentError, match="MODEL_BUDGET_EXHAUSTED"):
        await ledger.run("over-budget", "model", success)
    for index in range(3):
        await ledger.run(f"report-{index}", "model", success, reserve_model=2 - index)
    with pytest.raises(AgentError, match="MODEL_BUDGET_EXHAUSTED"):
        await ledger.run("ninth", "model", success, reserve_model=0)
    for index in range(3):
        await ledger.run(f"retrieval-{index}", "retrieval", success)
    with pytest.raises(AgentError, match="RETRIEVAL_BUDGET_EXHAUSTED"):
        await ledger.run("fourth-search", "retrieval", success)
    assert store.get(task_id)["_agent"]["counts"]["model"] == 8


async def test_failures_and_explicit_retry_both_consume_budget_without_leaking_provider_text():
    store, task_id, ledger = await prepared()
    calls = []

    async def failed():
        calls.append(1)
        raise ModelError("MODEL_HTTP_ERROR", 429)

    with pytest.raises(ModelError):
        await ledger.run("request", "model", failed)
    with pytest.raises(AgentError, match="MODEL_HTTP_ERROR"):
        await ledger.run("request", "model", failed)
    assert len(calls) == 1
    await ledger.run("request", "model", success, attempt=2)
    assert store.get(task_id)["_agent"]["counts"]["model"] == 2
    with pytest.raises(AgentError, match="CALL_ATTEMPT_INVALID"):
        await ledger.run("request", "model", success, attempt=3)


async def test_only_one_structure_repair_is_allowed_per_business_node():
    _, _, ledger = await prepared()
    await ledger.run("repair-one", "model", success, repair=True)
    with pytest.raises(AgentError, match="STRUCTURE_REPAIR_EXHAUSTED"):
        await ledger.run("repair-two", "model", success, repair=True)
    ledger.node_key = "amount"
    await ledger.run("amount-repair", "model", success, repair=True)


async def test_reserved_request_is_not_duplicated_concurrently_or_after_cancellation():
    store, task_id, ledger = await prepared()
    entered = asyncio.Event()

    async def interrupted():
        entered.set()
        await asyncio.Event().wait()

    operation = asyncio.create_task(ledger.run("ambiguous", "model", interrupted))
    await entered.wait()
    with pytest.raises(AgentError, match="MODEL_CALL_AMBIGUOUS"):
        await ledger.run("ambiguous", "model", success)
    operation.cancel()
    with pytest.raises(asyncio.CancelledError):
        await operation
    resumed = TaskLedger(store, task_id)
    with pytest.raises(AgentError, match="MODEL_CALL_AMBIGUOUS"):
        await resumed.run("ambiguous", "model", success)
    await resumed.run("ambiguous", "model", success, attempt=2)
    assert store.get(task_id)["_agent"]["counts"]["model"] == 2

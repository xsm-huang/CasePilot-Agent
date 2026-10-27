"""V1 public protocol over actual PostgreSQL with explicit injected provider doubles."""

import concurrent.futures
import time
from uuid import uuid4

import pytest
from casepilot.schemas.workspace import V1AnalysisTask, WorkspaceEvent
from workspace_fixtures import new_task, settle
from workspace_fixtures import workspace as workspace

pytestmark = pytest.mark.database


def test_v1_report_and_followup_have_separate_tasks_and_completed_context(workspace):
    client, app, chat = workspace
    conversation, created = new_task(client)
    task = settle(client, created["id"], "completed")
    V1AnalysisTask.model_validate(task)
    assert task["schemaVersion"] == 1
    assert [s["sectionKey"] for s in task["sections"]] == ["summary", "findings", "recommendations"]
    assert task["assistantMessageId"]
    assert task["report"]["sections"] == task["sections"]
    assert len(chat.calls) == 5
    current = client.get(f"/api/conversations/{conversation['id']}").json()
    assert [m["role"] for m in current["messages"]] == ["user", "assistant"]
    assert current["activeAnalysisId"] is None
    response = client.post(
        "/api/analyses",
        json={
            "conversationId": conversation["id"],
            "kind": "followup",
            "question": "还缺什么材料？",
        },
        headers={"Idempotency-Key": "followup-1"},
    )
    assert response.status_code == 202, response.text
    followup = settle(client, response.json()["id"], "completed")
    assert followup["id"] != task["id"]
    assert followup["context"]["generationId"] == task["context"]["generationId"]
    assert followup["context"]["messageIds"] == [m["id"] for m in current["messages"]]
    assert (
        app.state.store.get(followup["id"])["_agent"]["context"]["history"] == current["messages"]
    )
    assert client.get(f"/api/analyses/{task['id']}").json() == task


def test_review_is_checkpointed_versioned_and_idempotent(workspace):
    client, _, _ = workspace
    conversation, created = new_task(client, "CASE-2026-001")
    task = settle(client, created["id"], "waiting_review")
    assert task["report"] is None and not task["sections"]
    assert task["pendingReview"]["checkpointId"]
    assert task["pendingReview"]["revision"] == task["revision"]
    body = {
        "decision": "approve",
        "comment": "保留疑点继续",
        "interruptKey": task["pendingReview"]["interruptKey"],
        "expectedRevision": task["revision"],
    }
    path = f"/api/analyses/{task['id']}/review"
    stale = client.post(
        path,
        json=body | {"expectedRevision": task["revision"] - 1},
        headers={"Idempotency-Key": "stale"},
    )
    assert stale.status_code == 409
    accepted = client.post(path, json=body, headers={"Idempotency-Key": "review-1"})
    assert accepted.status_code == 202, accepted.text
    assert (
        client.post(path, json=body, headers={"Idempotency-Key": "review-1"}).json()
        == accepted.json()
    )
    assert (
        client.post(
            path, json=body | {"decision": "reject"}, headers={"Idempotency-Key": "review-1"}
        ).status_code
        == 409
    )
    final = settle(client, task["id"], "completed")
    assert final["ruleFindings"] == task["ruleFindings"]
    assert final["report"]["reviewerComment"] == body["comment"]
    assert len([e for e in final["execution"]["timeline"] if e["type"] == "report.completed"]) == 1
    assert client.get(f"/api/conversations/{conversation['id']}").json()["activeAnalysisId"] is None


def test_idempotent_create_precedes_active_conflict_and_failures_leave_no_message(workspace):
    client, _, _ = workspace
    conversation = client.post("/api/cases/CASE-2026-001/conversations", json={}).json()
    body = {"conversationId": conversation["id"], "kind": "initial"}
    first = client.post("/api/analyses", json=body, headers={"Idempotency-Key": "create-1"})
    assert first.status_code == 202, first.text
    assert (
        client.post("/api/analyses", json=body, headers={"Idempotency-Key": "create-1"}).json()
        == first.json()
    )
    assert (
        client.post("/api/analyses", json=body, headers={"Idempotency-Key": "another"}).status_code
        == 409
    )
    assert (
        client.post(
            "/api/analyses",
            json=body | {"question": "different"},
            headers={"Idempotency-Key": "create-1"},
        ).status_code
        == 409
    )
    current = client.get(f"/api/conversations/{conversation['id']}").json()
    assert len(current["messages"]) == 1


def test_recover_reuses_committed_summary_without_resetting_budget(workspace):
    client, app, chat = workspace
    chat.fail_section = "findings"
    conversation, created = new_task(client)
    partial = settle(client, created["id"], "recoverable")
    assert [s["sectionKey"] for s in partial["sections"]] == ["summary"]
    assert partial["report"] is None and partial["assistantMessageId"] is None
    before = app.state.store.get(partial["id"])["_agent"]["counts"]["model"]
    assert len(client.get(f"/api/conversations/{conversation['id']}").json()["messages"]) == 1
    # If command acknowledgement was interrupted after failure persisted, polling
    # must acknowledge it without replaying provider effects or changing the error.
    pending_command = next(
        c for c in app.state.store.commands.values() if c["taskId"] == partial["id"]
    )
    count_before_replay = len(chat.calls)
    client.portal.call(app.state.executor.execute, pending_command)
    assert len(chat.calls) == count_before_replay
    assert client.get(f"/api/analyses/{partial['id']}").json() == partial
    response = client.post(
        f"/api/analyses/{partial['id']}/recover",
        json={"expectedRevision": partial["revision"]},
        headers={"Idempotency-Key": "recover-1"},
    )
    assert response.status_code == 202, response.text
    final = settle(client, partial["id"], "completed")
    assert final["sections"][0] == partial["sections"][0]
    assert sum(call["section"] == "summary" for call in chat.calls) == 1
    assert app.state.store.get(final["id"])["_agent"]["counts"]["model"] == before + 2
    assert len(client.get(f"/api/conversations/{conversation['id']}").json()["messages"]) == 2


def test_persisted_sse_cursor_and_task_bound_citation(workspace):
    client, _, _ = workspace
    _, created = new_task(client)
    task = settle(client, created["id"], "completed")
    timeline = task["execution"]["timeline"]
    assert [e["seq"] for e in timeline] == list(range(1, task["lastEventSeq"] + 1))
    for event in timeline:
        WorkspaceEvent.model_validate(event)
    path = f"/api/analyses/{task['id']}/events"
    response = client.get(
        path + "?after=0", headers={"Last-Event-ID": str(task["lastEventSeq"] - 1)}
    )
    assert response.status_code == 200
    assert response.text.count("event: timeline") == 1
    assert "report.completed" in response.text
    assert client.get(path + f"?after={task['lastEventSeq']}").text == ""
    assert client.get(path + f"?after={task['lastEventSeq'] + 1}").status_code == 409
    for invalid in ("-1", "01", "abc", "9007199254740992"):
        assert client.get(path + "?after=" + invalid).status_code == 400
    citation = task["citations"][0]
    assert (
        client.get(f"/api/analyses/{task['id']}/citations/{citation['citationId']}").json()
        == citation
    )
    assert client.get(f"/api/analyses/{task['id']}/citations/not-related").status_code == 404


def test_concurrent_approve_reject_accepts_exactly_one_decision(workspace):
    client, _, _ = workspace
    _, created = new_task(client, "CASE-2026-001")
    task = settle(client, created["id"], "waiting_review")

    def decide(decision):
        return client.post(
            f"/api/analyses/{task['id']}/review",
            json={
                "decision": decision,
                "comment": decision,
                "interruptKey": task["pendingReview"]["interruptKey"],
                "expectedRevision": task["revision"],
            },
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code

    with concurrent.futures.ThreadPoolExecutor() as pool:
        statuses = list(pool.map(decide, ["approve", "reject"]))
    assert sorted(statuses) == [202, 409]
    assert settle(client, task["id"])["status"] in {"completed", "rejected"}


def test_live_partial_report_is_visible_before_final_answer(workspace):
    client, _, chat = workspace
    chat.block_section = "findings"
    try:
        conversation, created = new_task(client)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            partial = client.get(f"/api/analyses/{created['id']}").json()
            if partial["sections"]:
                break
            time.sleep(0.02)
        assert partial["status"] == "running"
        assert [s["sectionKey"] for s in partial["sections"]] == ["summary"]
        assert partial["report"] is None and partial["assistantMessageId"] is None
        assert len(client.get(f"/api/conversations/{conversation['id']}").json()["messages"]) == 1
    finally:
        chat.release.set()
    final = settle(client, created["id"], "completed")
    assert final["sections"][0] == partial["sections"][0]


def test_legacy_snapshot_is_unchanged_and_write_routes_are_blocked(workspace):
    from casepilot.analyses.store import Store
    from casepilot.persistence.workspace_repository import WorkspaceRepository

    client, app, _ = workspace

    async def legacy_fixture():
        legacy_store = Store(app.state.store.pool, app.state.store.schema)
        await legacy_store.setup()
        created = await legacy_store.create("CASE-2026-002")
        legacy = await legacy_store.mutate(created["id"], {"status": "completed"})
        app.state.store.tasks[legacy["id"]] = legacy
        repo = WorkspaceRepository(app.state.store.pool, app.state.store.schema)
        tasks, _ = await repo.load()  # Repeated migration must preserve task JSONB.
        assert tasks[legacy["id"]] == legacy
        return legacy

    original = client.portal.call(legacy_fixture)
    task = client.get(f"/api/analyses/{original['id']}").json()
    assert task["schemaVersion"] == 0 and task["readOnly"] is True
    for route, body in (
        (
            "review",
            {"decision": "approve", "comment": "", "interruptKey": "old", "expectedRevision": 0},
        ),
        ("recover", {"expectedRevision": 0}),
    ):
        response = client.post(
            f"/api/analyses/{original['id']}/{route}", json=body, headers={"Idempotency-Key": route}
        )
        assert response.status_code == 409
        assert response.json()["code"] == "LEGACY_READ_ONLY"
    assert client.get(f"/api/analyses/{original['id']}/events").status_code == 409
    assert app.state.store.get(original["id"]) == original


def test_knowledge_preflight_failure_does_not_create_orphan_message_or_task(workspace):
    client, app, chat = workspace
    conversation = client.post("/api/cases/CASE-2026-002/conversations", json={}).json()

    async def unpublish():
        repository = app.state.knowledge.repository
        async with repository.pool.connection() as conn:
            await conn.execute(repository.sql("DELETE FROM {s}.knowledge_publications"))

    client.portal.call(unpublish)
    response = client.post(
        "/api/analyses",
        json={"conversationId": conversation["id"], "kind": "initial"},
        headers={"Idempotency-Key": "no-index"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "KNOWLEDGE_NOT_READY"
    assert not client.get(f"/api/conversations/{conversation['id']}").json()["messages"]
    assert not client.get("/api/analyses").json()
    assert not chat.calls


def test_failed_turn_is_excluded_from_followup_context(workspace):
    client, app, chat = workspace
    conversation, created = new_task(client)
    completed = settle(client, created["id"], "completed")
    chat.invalid_section = "summary"
    failed = client.post(
        "/api/analyses",
        json={"conversationId": conversation["id"], "kind": "followup", "question": "失败回合"},
        headers={"Idempotency-Key": "failed-turn"},
    ).json()
    interrupted = settle(client, failed["id"], "failed")
    assert interrupted["error"]["code"] == "REPORT_OUTPUT_INVALID"
    assert app.state.store.get(failed["id"])["_agent"]["counts"]["repair"] == 1
    chat.invalid_section = None
    response = client.post(
        "/api/analyses",
        json={
            "conversationId": conversation["id"],
            "kind": "followup",
            "question": "只使用已完成回合",
        },
        headers={"Idempotency-Key": "after-failure"},
    )
    assert response.status_code == 202, response.text
    final = settle(client, response.json()["id"], "completed")
    assert final["context"]["messageIds"] == [
        completed["userMessageId"],
        completed["assistantMessageId"],
    ]
    assert interrupted["userMessageId"] not in final["context"]["messageIds"]


@pytest.mark.parametrize("failure", ["database", "pool"])
def test_storage_outage_returns_safe_retryable_http_error(workspace, monkeypatch, failure):
    from psycopg import OperationalError
    from psycopg_pool import PoolTimeout

    client, app, _ = workspace
    conversation = client.post("/api/cases/CASE-2026-002/conversations", json={}).json()

    async def unavailable(*args, **kwargs):
        raise (OperationalError if failure == "database" else PoolTimeout)(
            "private-connection-password"
        )

    monkeypatch.setattr(app.state.store.repository, "messages", unavailable)
    response = client.get(f"/api/conversations/{conversation['id']}")
    assert response.status_code == 503
    assert response.json()["code"] == "DEPENDENCY_UNAVAILABLE"
    assert response.json()["requestId"]
    assert "private-connection-password" not in response.text

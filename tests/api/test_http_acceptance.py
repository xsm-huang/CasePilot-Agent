"""V1 over actual TCP: live paused stream, replay, rejection and isolation."""

import concurrent.futures
from uuid import uuid4

import httpx
import pytest
from conftest import ROOT, ApiProcess, sse_events
from workspace_fixtures import new_task, seed_knowledge, settle

pytestmark = pytest.mark.database


@pytest.fixture
def tcp_workspace(postgres_env):
    server = ApiProcess(postgres_env, ROOT / "tests/api/workspace_api_worker.py").start()
    try:
        with httpx.Client(base_url=server.base.removesuffix("/api"), timeout=15) as api:
            seed_knowledge(api)
            yield api, server
    finally:
        server.stop()


def decision(api, task, value="approve"):
    return api.post(
        f"/api/analyses/{task['id']}/review",
        json={
            "decision": value,
            "comment": "核验意见",
            "interruptKey": task["pendingReview"]["interruptKey"],
            "expectedRevision": task["revision"],
        },
        headers={"Idempotency-Key": str(uuid4())},
    )


def test_cases_and_error_boundaries(tcp_workspace):
    api, _ = tcp_workspace
    cases = api.get("/api/cases").json()
    assert len(cases) == 2
    assert api.get("/api/cases/missing").status_code == 404
    assert api.get("/api/analyses/missing").status_code == 404
    for body in ({}, {"caseId": "CASE-2026-001"}, [], "case"):
        response = api.post("/api/analyses", json=body)
        assert response.status_code == 400
        assert response.json()["requestId"]
    assert (
        api.post(
            "/api/analyses", content="{", headers={"Content-Type": "application/json"}
        ).status_code
        == 400
    )


def test_sse_live_before_completion_and_cursor_replay(tcp_workspace):
    api, _ = tcp_workspace
    _, created = new_task(api, "CASE-2026-001")
    paused = settle(api, created["id"], "waiting_review")
    assert paused["report"] is None
    cursor = paused["lastEventSeq"]
    with api.stream(
        "GET",
        f"/api/analyses/{paused['id']}/events?after=0",
        headers={"Last-Event-ID": str(cursor - 1)},
    ) as response:
        assert response.status_code == 200
        stream = sse_events(response)
        assert next(stream)["seq"] == cursor
        assert api.get(f"/api/analyses/{paused['id']}").json()["status"] == "waiting_review"
        assert decision(api, paused).status_code == 202
        tail = list(stream)
    result = settle(api, paused["id"], "completed")
    assert tail == result["execution"]["timeline"][cursor:]
    assert tail[-1]["type"] == "report.completed"
    assert [e["seq"] for e in tail] == list(range(cursor + 1, result["lastEventSeq"] + 1))
    with api.stream("GET", f"/api/analyses/{paused['id']}/events?after={cursor}") as response:
        assert list(sse_events(response)) == tail
    with api.stream(
        "GET", f"/api/analyses/{paused['id']}/events?after={result['lastEventSeq']}"
    ) as response:
        assert list(sse_events(response)) == []


def test_reject_has_no_report_and_other_conversation_is_independent(tcp_workspace):
    api, server = tcp_workspace

    def run(case_id):
        with httpx.Client(base_url=server.base.removesuffix("/api"), timeout=15) as client:
            _, created = new_task(client, case_id)
            return settle(client, created["id"])

    with concurrent.futures.ThreadPoolExecutor() as pool:
        risky, normal = list(pool.map(run, ["CASE-2026-001", "CASE-2026-002"]))
    assert normal["status"] == "completed"
    assert risky["status"] == "waiting_review"
    assert decision(api, risky, "reject").status_code == 202
    rejected = settle(api, risky["id"], "rejected")
    assert rejected["report"] is None and rejected["assistantMessageId"] is None
    assert not rejected["sections"]
    assert api.get(f"/api/analyses/{normal['id']}").json() == normal


@pytest.mark.parametrize("cursor", ["-1", "abc", "1.5", "9007199254740992"])
def test_invalid_event_cursor(tcp_workspace, cursor):
    api, _ = tcp_workspace
    _, created = new_task(api)
    task = settle(api, created["id"])
    response = api.get(f"/api/analyses/{task['id']}/events", headers={"Last-Event-ID": cursor})
    assert response.status_code == 400

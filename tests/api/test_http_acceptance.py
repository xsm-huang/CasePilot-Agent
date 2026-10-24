"""Deterministic V0 migration checks over a real TCP / uvicorn process.

These tests do not prove real LLM, embeddings, vector retrieval or V1 reporting.
"""

import concurrent.futures

import httpx
import pytest
from conftest import create_settled, settle_task, sse_events


def test_cases_and_error_boundaries(api):
    cases = api.get("/cases").json()
    assert [claim["id"] for claim in cases] == ["CASE-2026-001", "CASE-2026-002"]
    assert api.get("/cases/CASE-2026-001").json() == cases[0]
    assert api.get("/cases/missing").status_code == 404
    assert api.get("/analyses/missing").status_code == 404
    assert api.post("/analyses", json={"caseId": "missing"}).status_code == 404
    for body in ({}, {"caseId": 4}, None, [], "case"):
        assert api.post("/analyses", json=body).status_code == 400
    assert (
        api.post("/analyses", content="{", headers={"Content-Type": "application/json"}).status_code
        == 400
    )


def test_pause_approve_and_duplicate_guard(api):
    task = create_settled(api)
    assert task["status"] == "waiting_review"
    assert task.get("report") is None
    assert [f["code"] for f in task["findings"]] == [
        "MISSING_REPAIR_INVOICE",
        "ACCIDENT_BEFORE_POLICY",
    ]
    assert all(f["source"] == "rule" for f in task["findings"])
    assert {c["id"] for c in task["citations"]} == {"AUTO-2025-01-04", "AUTO-2025-01-18"}
    path = f"/analyses/{task['id']}/review"
    for body in (
        {},
        {"decision": "invalid"},
        {"decision": "approve", "comment": 1},
        {"decision": "approve", "comment": "x" * 2001},
    ):
        assert api.post(path, json=body).status_code == 400
    assert api.post(path, json={"decision": "approve", "comment": "核验后继续"}).is_success
    result = settle_task(api, task["id"])
    assert result["id"] == task["id"]
    assert result["status"] == "completed"
    assert result["report"]["reviewerComment"] == "核验后继续"
    assert result["report"]["findings"] == task["findings"]
    assert sum(e["type"] == "review_required" for e in result["events"]) == 1
    assert sum(e["type"] == "tool" for e in result["events"]) == 3
    assert api.post(path, json={"decision": "approve"}).status_code == 409


def test_reject_has_no_report(api):
    task = create_settled(api)
    assert api.post(
        f"/analyses/{task['id']}/review", json={"decision": "reject", "comment": "补材料"}
    ).is_success
    result = settle_task(api, task["id"])
    assert result["status"] == "rejected"
    assert result.get("report") is None
    assert result["events"][-1]["status"] == "rejected"


def test_clean_case_and_parallel_task_isolation(api, api_process):
    def run(case_id):
        with httpx.Client(base_url=api_process.base, timeout=5) as client:
            return create_settled(client, case_id)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        risky, normal = list(pool.map(run, ["CASE-2026-001", "CASE-2026-002"]))
    assert risky["id"] != normal["id"]
    assert risky["status"] == "waiting_review"
    assert normal["status"] == "completed"
    assert normal["findings"] == []
    assert normal["report"]["caseId"] == "CASE-2026-002"
    assert [c["id"] for c in normal["report"]["citations"]] == ["AUTO-2025-01-22"]
    assert risky["id"] in {t["id"] for t in api.get("/analyses").json()}


def test_sse_live_before_completion_and_cursor_replay(api):
    task = create_settled(api)
    cursor = task["events"][-1]["id"]
    # Opening stream must deliver headers while task is paused. A buffered ASGI
    # transport would deadlock here; this test uses a separate server process.
    with api.stream(
        "GET", f"/analyses/{task['id']}/events", headers={"Last-Event-ID": str(cursor - 1)}
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        stream = sse_events(response)
        assert next(stream)["id"] == cursor
        assert api.get(f"/analyses/{task['id']}").json()["status"] == "waiting_review"
        assert api.post(f"/analyses/{task['id']}/review", json={"decision": "approve"}).is_success
        tail = list(stream)
    assert [e["id"] for e in tail] == [cursor + 1, cursor + 2]
    assert tail[-1]["type"] == "report"
    assert tail[-1]["status"] == "completed"
    snapshot = api.get(f"/analyses/{task['id']}").json()
    assert tail == [event for event in snapshot["events"] if event["id"] > cursor]
    with api.stream(
        "GET", f"/analyses/{task['id']}/events", headers={"Last-Event-ID": str(cursor)}
    ) as response:
        assert list(sse_events(response)) == tail
    with api.stream(
        "GET", f"/analyses/{task['id']}/events", headers={"Last-Event-ID": str(cursor + 2)}
    ) as response:
        assert list(sse_events(response)) == []


@pytest.mark.parametrize("cursor", ["-1", "abc", "1.5", "9007199254740992"])
def test_invalid_event_cursor(api, cursor):
    task = create_settled(api, "CASE-2026-002")
    with api.stream(
        "GET", f"/analyses/{task['id']}/events", headers={"Last-Event-ID": cursor}
    ) as response:
        assert response.status_code == 400

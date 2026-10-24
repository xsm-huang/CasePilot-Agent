"""Actual PostgreSQL/checkpointer + killed-process recovery. No real models.

Enable explicitly with CASEPILOT_TEST_DATABASE_URL. Only UUID-owned schemas
are dropped; existing application schemas, volumes and containers are untouched.
"""

from __future__ import annotations

import concurrent.futures

import httpx
import pytest
from conftest import ApiProcess, create_settled, settle_task, sse_events

pytestmark = pytest.mark.database


def kill_process(server):
    # A forced kill is intentional: a graceful app restart alone is weaker evidence.
    server.process.kill()
    server.process.wait(timeout=5)


def test_waiting_review_survives_killed_process_and_only_one_decision(postgres_env):
    first = ApiProcess(postgres_env).start()
    try:
        with httpx.Client(base_url=first.base, timeout=5) as api:
            paused = create_settled(api)
            assert paused["status"] == "waiting_review"
            assert paused.get("report") is None
        kill_process(first)
    finally:
        first.stop()

    second = ApiProcess(postgres_env).start()
    try:
        with httpx.Client(base_url=second.base, timeout=5) as api:
            restored = api.get(f"/analyses/{paused['id']}").json()
            assert restored == paused

            def decide(decision):
                with httpx.Client(base_url=second.base, timeout=10) as concurrent_api:
                    response = concurrent_api.post(
                        f"/analyses/{paused['id']}/review",
                        json={"decision": decision, "comment": "恢复验证"},
                    )
                    return decision, response.status_code

            with concurrent.futures.ThreadPoolExecutor() as pool:
                responses = list(pool.map(decide, ["approve", "reject"]))
            assert sum(status in (200, 201, 202) for _, status in responses) == 1, responses
            assert sum(status == 409 for _, status in responses) == 1, responses
            winner = next(decision for decision, status in responses if status in (200, 201, 202))
            result = settle_task(api, paused["id"])
            assert result["status"] == ("completed" if winner == "approve" else "rejected")
            assert result["findings"] == paused["findings"]
            assert result["citations"] == paused["citations"]
            assert result["events"][: len(paused["events"])] == paused["events"]
            assert [e["id"] for e in result["events"]] == list(range(1, len(result["events"]) + 1))
            assert sum(e["type"] == "review_required" for e in result["events"]) == 1
            assert sum(e["type"] == "tool" for e in result["events"]) == 3
            assert sum(e["type"] == "report" for e in result["events"]) == (
                1 if winner == "approve" else 0
            )
            with api.stream(
                "GET",
                f"/analyses/{paused['id']}/events",
                headers={"Last-Event-ID": str(paused["events"][-1]["id"])},
            ) as response:
                assert list(sse_events(response)) == result["events"][len(paused["events"]) :]
    finally:
        second.stop()

    third = ApiProcess(postgres_env).start()
    try:
        with httpx.Client(base_url=third.base, timeout=5) as api:
            assert api.get(f"/analyses/{paused['id']}").json() == result
            assert (
                api.post(
                    f"/analyses/{paused['id']}/review", json={"decision": "approve"}
                ).status_code
                == 409
            )
    finally:
        third.stop()

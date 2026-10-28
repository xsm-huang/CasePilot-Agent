"""V1 official checkpointer survives forced process termination."""

import concurrent.futures

import httpx
import pytest
from conftest import ROOT, ApiProcess, sse_events
from test_http_acceptance import decision
from workspace_fixtures import new_task, seed_knowledge, settle

pytestmark = pytest.mark.database


def test_waiting_review_survives_killed_process_and_only_one_decision(postgres_env):
    worker = ROOT / "tests/api/workspace_api_worker.py"
    first = ApiProcess(postgres_env, worker).start()
    try:
        with httpx.Client(base_url=first.base.removesuffix("/api"), timeout=15) as api:
            seed_knowledge(api)
            _, created = new_task(api, "C03")
            paused = settle(api, created["id"], "waiting_review")
        first.process.kill()
        first.process.wait(timeout=5)
    finally:
        first.stop()
    second = ApiProcess(postgres_env, worker).start()
    try:
        with httpx.Client(base_url=second.base.removesuffix("/api"), timeout=15) as api:
            assert api.get(f"/api/analyses/{paused['id']}").json() == paused

            def decide(value):
                with httpx.Client(base_url=second.base.removesuffix("/api"), timeout=15) as client:
                    return value, decision(client, paused, value).status_code

            with concurrent.futures.ThreadPoolExecutor() as pool:
                responses = list(pool.map(decide, ["approve", "reject"]))
            assert sorted(status for _, status in responses) == [202, 409]
            winner = next(value for value, status in responses if status == 202)
            result = settle(api, paused["id"], "completed" if winner == "approve" else "rejected")
            assert result["ruleFindings"] == paused["ruleFindings"]
            assert result["citations"] == paused["citations"]
            assert (
                result["execution"]["timeline"][: paused["lastEventSeq"]]
                == paused["execution"]["timeline"]
            )
            assert sum(e["type"] == "review.required" for e in result["execution"]["timeline"]) == 1
            with api.stream(
                "GET", f"/api/analyses/{paused['id']}/events?after={paused['lastEventSeq']}"
            ) as response:
                assert (
                    list(sse_events(response))
                    == result["execution"]["timeline"][paused["lastEventSeq"] :]
                )
    finally:
        second.stop()
    third = ApiProcess(postgres_env, worker).start()
    try:
        with httpx.Client(base_url=third.base.removesuffix("/api"), timeout=15) as api:
            assert api.get(f"/api/analyses/{paused['id']}").json() == result
            assert decision(api, paused).status_code == 409
    finally:
        third.stop()

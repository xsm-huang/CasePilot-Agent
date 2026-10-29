"""Actual killed-process windows, never an in-process exception masquerading as restart."""

import concurrent.futures
import time

import httpx
import psycopg
import pytest
from conftest import ROOT, ApiProcess, sse_events
from psycopg import sql
from test_http_acceptance import decision
from workspace_fixtures import new_task, seed_knowledge, settle

pytestmark = pytest.mark.database


@pytest.mark.parametrize(
    "stage",
    ["review_accepted", "checkpoint_before_projection", "report_saved", "model_returned"],
)
def test_killed_process_windows_preserve_effects_and_budget(postgres_env, tmp_path, stage):
    marker = tmp_path / "boundary.txt"
    environment = postgres_env | {
        "WORKSPACE_FAULT_STAGE": stage,
        "WORKSPACE_FAULT_MARKER": str(marker),
    }
    first = ApiProcess(environment, ROOT / "tests/api/workspace_fault_worker.py").start()
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    pending = None
    try:
        with httpx.Client(base_url=first.base.removesuffix("/api"), timeout=30) as api:
            seed_knowledge(api)
            _, created = new_task(api, "C02")
            if stage in {"review_accepted", "report_saved"}:
                paused = settle(api, created["id"], "waiting_review")
                pending = pool.submit(decision, api, paused)
            deadline = time.monotonic() + 15
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            assert marker.exists(), first.diagnostics()
            assert marker.read_text() == created["id"]
            with psycopg.connect(postgres_env["DATABASE_URL"]) as conn:
                before = conn.execute(
                    sql.SQL("SELECT snapshot FROM {}.tasks WHERE id=%s").format(
                        sql.Identifier(postgres_env["CASEPILOT_DB_SCHEMA"])
                    ),
                    (created["id"],),
                ).fetchone()[0]
            first.process.kill()
            first.process.wait(timeout=5)
    finally:
        first.stop()
        if pending:
            try:
                pending.result(timeout=5)
            except httpx.HTTPError:
                pass  # The server was intentionally killed before its HTTP response.
        pool.shutdown(wait=True)
    second = ApiProcess(postgres_env, ROOT / "tests/api/workspace_api_worker.py").start()
    try:
        with httpx.Client(base_url=second.base.removesuffix("/api"), timeout=15) as api:
            restored = settle(api, created["id"])
            if stage == "model_returned":
                assert restored["status"] == "recoverable"
                assert restored["error"]["code"] == "MODEL_CALL_AMBIGUOUS"
                assert restored["report"]["kind"] == "stage"
                assert (
                    api.post(
                        f"/api/analyses/{created['id']}/recover",
                        json={"expectedRevision": restored["revision"]},
                        headers={"Idempotency-Key": "explicit-recovery"},
                    ).status_code
                    == 202
                )
            restored = settle(api, created["id"])
            if restored["status"] == "waiting_review":
                assert restored["status"] == "waiting_review"
                assert restored["pendingReview"]["checkpointId"]
                assert decision(api, restored).status_code == 202
            final = settle(api, created["id"], "completed")
            assert final["execution"]["timeline"][: len(before["events"])] == before["events"]
            assert final["report"]["kind"] == "final"
            assert sum(e["type"] == "report.completed" for e in final["execution"]["timeline"]) == 1
            assert sum(e["type"] == "report.saved" for e in final["execution"]["timeline"]) == (3 if stage == "model_returned" else 2)
            if stage == "report_saved":
                assert final["report"] == before["report"]
            with psycopg.connect(postgres_env["DATABASE_URL"]) as conn:
                saved = conn.execute(
                    sql.SQL("SELECT snapshot FROM {}.tasks WHERE id=%s").format(
                        sql.Identifier(postgres_env["CASEPILOT_DB_SCHEMA"])
                    ),
                    (created["id"],),
                ).fetchone()[0]
            assert saved["_agent"]["counts"]["model"] == (5 if stage == "model_returned" else 4)
            assert saved["_agent"]["counts"]["model"] >= before["_agent"]["counts"]["model"]
            with api.stream(
                "GET", f"/api/analyses/{created['id']}/events?after={len(before['events'])}"
            ) as response:
                assert (
                    list(sse_events(response))
                    == final["execution"]["timeline"][len(before["events"]) :]
                )
    finally:
        second.stop()

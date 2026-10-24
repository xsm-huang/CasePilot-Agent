"""Kill a real indexing process; boot the production API to reconcile phases."""

import os
import subprocess
import sys
import time

import httpx
import pytest
from casepilot.knowledge.service import KnowledgeService
from conftest import ROOT, ApiProcess
from pdf_fixtures import text_pdf
from test_knowledge_database import FakeEmbedding, publish, run_database

pytestmark = pytest.mark.database


@pytest.mark.parametrize("phase", ["parsing", "chunking", "embedding"])
def test_killed_indexing_is_failed_on_actual_api_boot_and_explicit_retry(
    postgres_env, tmp_path, phase
):
    state = {}

    async def prepare(repo):
        service = KnowledgeService(repo, FakeEmbedding())
        state["old"] = await publish(service)
        state["candidate"] = await service.import_document(
            "replacement.pdf",
            text_pdf(["New replacement clause"]),
            "AUTO",
            "2025-01",
            state["old"]["generationId"],
        )

    run_database(postgres_env, prepare)

    marker = tmp_path / "durable-phase.txt"
    environment = os.environ.copy()
    environment.update(postgres_env)
    environment["PYTHONPATH"] = str(ROOT / "apps/api/src")
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "tests/api/knowledge_worker.py"), phase, str(marker)],
        env=environment,
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 30
        while not marker.exists() and time.monotonic() < deadline:
            assert process.poll() is None, (
                "Test indexing component exited before durable phase barrier"
            )
            time.sleep(0.03)
        assert marker.exists(), f"Indexing never reached phase {phase}"
        assert marker.read_text(encoding="utf-8") == state["candidate"]["generationId"]
        process.kill()
        process.wait(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)

    server = ApiProcess(postgres_env).start()
    try:
        with httpx.Client(base_url=server.base, timeout=5) as client:
            response = client.get(f"/knowledge/generations/{state['candidate']['generationId']}")
            assert response.status_code == 200, response.text
            interrupted = response.json()
            assert interrupted["status"] == "failed"
            assert interrupted["error"]["code"] == "INDEXING_INTERRUPTED"
            assert interrupted["isActive"] is False
            assert interrupted["attempt"] == 1
            assert interrupted["attempts"][0]["status"] == "failed"
            old = client.get(f"/knowledge/generations/{state['old']['generationId']}").json()
            assert old["isActive"] is True
    finally:
        server.stop()

    async def retry(repo):
        service = KnowledgeService(repo, FakeEmbedding())
        result = await service.retry(interrupted["generationId"], interrupted["revision"])
        assert result["attempt"] == 2
        assert result["attempts"][0]["error"]["code"] == "INDEXING_INTERRUPTED"
        assert await service.process_next() is True
        completed = await service.get_generation(interrupted["generationId"])
        assert completed["status"] == "ready"
        assert completed["isActive"] is True

    run_database(postgres_env, retry)


def test_queued_work_remains_queued_during_reconciliation_and_continues(postgres_env):
    async def scenario(repo):
        service = KnowledgeService(repo, FakeEmbedding())
        queued = await service.import_document(
            "queued.pdf", text_pdf(["Queued invoice clause"]), "AUTO", "2025-01"
        )
        await repo.reconcile()
        unchanged = await repo.get_generation(queued["generationId"])
        assert unchanged == queued
        assert await service.process_next() is True
        ready = await repo.get_generation(queued["generationId"])
        assert ready["status"] == "ready"
        assert ready["attempt"] == 1

    run_database(postgres_env, scenario)

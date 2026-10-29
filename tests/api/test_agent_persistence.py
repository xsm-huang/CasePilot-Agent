"""Actual PostgreSQL and separate killed processes; provider effects remain fake."""

import json
import os
import subprocess
import sys
import time

import pytest
from agent_fixtures import ScriptedChat, assessment
from casepilot.analyses.agent import run_agent_analysis
from casepilot.analyses.workspace_store import WorkspaceStore, fingerprint
from casepilot.cases.review_repository import get_review_case_input, review_scope_items
from casepilot.knowledge.config import PROFILE
from casepilot.knowledge.service import KnowledgeService
from casepilot.workflow.prompts import PROMPT_VERSION
from conftest import ROOT
from test_knowledge_database import FakeEmbedding, publish, run_database

pytestmark = pytest.mark.database


def test_g3_graph_consumes_real_pdf_pgvector_and_keeps_original_generation(postgres_env):
    async def scenario(repository):
        embedder = FakeEmbedding()
        knowledge = KnowledgeService(repository, embedder)
        generation = await publish(knowledge, product="AUTO-COMPREHENSIVE")
        rows = await repository.search(
            "AUTO-COMPREHENSIVE", "2025-01", generation["generationId"], [0.25] * 1024
        )
        store = WorkspaceStore(repository.pool, repository.schema)
        await store.setup()
        chat = ScriptedChat(assessments=[assessment(citation=rows[0]["chunkId"])])
        case = get_review_case_input("C02")
        binding = {
            "documentId": generation["documentId"],
            "documentSha256": generation["sha256"],
            "version": generation["clauseVersion"],
            "sectionIds": [],
            "status": "ready",
            "generationId": generation["generationId"],
            "productCode": generation["productCode"],
            "clauseVersion": generation["clauseVersion"],
            "embeddingProfile": PROFILE,
        }
        snapshot = {
            "snapshotKind": "closed_claim_review",
            "caseId": "C02",
            "caseRevision": case["caseRevision"],
            "preparedAt": case["preparedAt"],
            "payload": case,
            "scopeItems": review_scope_items(case),
            "knowledgeBindings": [binding],
        }
        context = {
            "caseId": "C02",
            "caseSnapshot": snapshot,
            "inputVersion": "test-input",
            "knowledgeBindings": [binding],
            "modelProfile": chat.config.chat_model,
            "promptVersion": PROMPT_VERSION,
        }
        conversation = await store.create_conversation("C02", "固定版本执行验收")
        body = dict(
            conversationId=conversation["id"],
            kind="initial",
            question="请核查案件事实、材料完整性及条款依据。",
        )
        task = await store.create_analysis(body, context, [], "create", fingerprint(body))
        result = await run_agent_analysis(store, task["id"], knowledge, chat)
        assert (
            result["context"]["knowledgeBindings"][0]["generationId"] == generation["generationId"]
        )
        assert result["citations"][0]["documentId"] == generation["documentId"]
        assert result["citations"][0]["page"] == 1
        assert result["citations"][0]["fileName"] == "self-authored.pdf"
        await publish(
            knowledge,
            text="Replacement clause with a different generation.",
            product="AUTO-COMPREHENSIVE",
            expected=generation["generationId"],
        )
        reloaded = WorkspaceStore(repository.pool, repository.schema)
        await reloaded.setup()
        before = len(embedder.calls), len(chat.calls)
        assert await run_agent_analysis(reloaded, task["id"], knowledge, chat) == result
        assert (len(embedder.calls), len(chat.calls)) == before

    run_database(postgres_env, scenario)


def test_accounting_survives_process_restart_and_ambiguous_call_is_not_free(postgres_env, tmp_path):
    environment = os.environ | postgres_env | {"PYTHONPATH": str(ROOT / "apps/api/src")}
    command = [sys.executable, str(ROOT / "tests/api/agent_ledger_worker.py")]

    def run(*arguments):
        process = subprocess.run(
            [*command, *arguments],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert process.returncode == 0, process.stderr.replace(
            postgres_env["DATABASE_URL"], "[redacted]"
        )[-2000:]
        return json.loads(process.stdout)

    task_id = run("seed")["taskId"]
    assert run("replay", task_id)["count"] == 1
    marker = tmp_path / "agent-call-reserved"
    worker = subprocess.Popen(
        [*command, "interrupt", task_id, str(marker)],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 20
        while not marker.exists() and time.monotonic() < deadline:
            assert worker.poll() is None, "Accounting worker failed before reserving the call"
            time.sleep(0.05)
        assert marker.exists(), "No durable reservation evidence within timeout"
        worker.kill()
        worker.wait(timeout=5)
    finally:
        if worker.poll() is None:
            worker.kill()
            worker.wait(timeout=5)
    assert run("recover", task_id)["count"] == 3

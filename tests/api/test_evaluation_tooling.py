"""Offline validation of frozen labels and the real acceptance request guard."""

import asyncio
import inspect
import json
import re
import sys
from types import SimpleNamespace

import httpx
import pytest
from casepilot.analyses.evidence import case_facts
from casepilot.cases.evidence_rules import evaluate_evidence_rules
from casepilot.cases.repository import get_case
from casepilot.knowledge.pdf import chunk_pages, parse_pages
from casepilot.model.errors import ModelError
from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_v1 import report_checks, report_plan
from evaluation import artifacts
from evaluation.budget import BudgetTransport
from evaluation.data import load, manifest
from evaluation.pdf import corpus_pdf
from evaluation.run_state import RunState, RunStateError

EXPECTED_DATA_HASHES = {
    "corpus.json": "e80cb37483926067155f6cda62b5991948de1fd3ec649dd464633eea72455d05",
    "reports.json": "c0d9550b43a381341051b5ca5207a5e0027217deac9038686d31a1c7383bba8f",
    "retrieval.json": "68a8080bc93aaa600293c5c84cd5dba760c89100b4b4b0f453169a130dfee395",
}


def test_frozen_dataset_has_required_labels_and_traceable_pdf_pages():
    corpus, queries, reports = (
        load(name) for name in ("corpus.json", "retrieval.json", "reports.json")
    )

    assert manifest() == EXPECTED_DATA_HASHES
    assert set(corpus) == {"title", "productCode", "clauseVersion", "pages"}
    assert all(isinstance(corpus[key], str) and corpus[key].strip() for key in corpus if key != "pages")
    assert len(corpus["pages"]) == 12
    assert all(isinstance(page, str) and page.strip() for page in corpus["pages"])

    assert len(queries) == 24
    assert {query["id"] for query in queries} == {f"R{index:02d}" for index in range(1, 25)}
    assert len({query["question"] for query in queries}) == len(queries)
    assert [
        sum(query["kind"] == kind for query in queries)
        for kind in ("answer", "isolation", "unanswerable")
    ] == [12, 6, 6]
    for query in queries:
        assert set(query) == {"id", "kind", "question", "pages"}
        assert re.fullmatch(r"R\d{2}", query["id"])
        assert isinstance(query["question"], str) and query["question"].strip()
        assert isinstance(query["pages"], list)
        if query["kind"] == "answer":
            assert query["pages"]
            assert len(query["pages"]) == len(set(query["pages"]))
            assert all(type(page) is int and 1 <= page <= len(corpus["pages"]) for page in query["pages"])
        else:
            assert query["kind"] in {"isolation", "unanswerable"}
            assert query["pages"] == []

    assert len(reports) == 10
    assert {report["id"] for report in reports} == {f"A{index:02d}" for index in range(1, 11)}
    assert len({report["question"] for report in reports}) == len(reports)
    for report in reports:
        assert set(report) == {"id", "caseId", "question", "rules", "insufficient"}
        assert re.fullmatch(r"A\d{2}", report["id"])
        assert isinstance(report["question"], str) and report["question"].strip()
        assert type(report["insufficient"]) is bool
        assert isinstance(report["rules"], list)
        assert len(report["rules"]) == len(set(report["rules"]))
        assert all(isinstance(code, str) and re.fullmatch(r"[A-Z][A-Z0-9_]*", code) for code in report["rules"])
        claim = get_case(report["caseId"])
        assert claim is not None, f"Unknown report caseId: {report['caseId']}"
        assert (claim["productCode"], claim["clauseVersion"]) == (
            corpus["productCode"],
            corpus["clauseVersion"],
        )
        actual_rules = {
            finding["code"]
            for finding in evaluate_evidence_rules(claim, case_facts(claim))
        }
        assert set(report["rules"]) <= actual_rules

    chunks = chunk_pages(parse_pages(corpus_pdf(corpus["pages"])))
    assert len(chunks) == 12
    assert [c["page"] for c in chunks] == list(range(1, 13))
    assert "Article 12." in chunks[-1]["content"]


def test_live_budget_pre_reserves_and_refuses_more_than_approved_requests(tmp_path):
    path = tmp_path / "calls.json"
    calls = []

    async def scenario():
        async def respond(request):
            # The durable reservation must exist before any provider effect.
            state = json.loads(path.read_text(encoding="utf-8"))
            assert state["used"]["model"] == 1
            assert state["calls"][0]["status"] == "reserved"
            calls.append(request)
            return httpx.Response(200, json={"usage": {"total_tokens": 12, "unsafe": "secret"}})

        budget = BudgetTransport(path, 1, 1, transport=httpx.MockTransport(respond))
        async with httpx.AsyncClient(transport=budget) as client:
            await client.post(
                "https://provider.invalid/chat/completions", json={"model": "glm-5.3-flash"}
            )
            with pytest.raises(ModelError, match="EVALUATION_BUDGET_EXHAUSTED"):
                await client.post(
                    "https://provider.invalid/chat/completions", json={"model": "glm-5.3-flash"}
                )
        assert len(calls) == 1
        assert budget.state["calls"][0]["usage"] == {"total_tokens": 12}
        assert "secret" not in path.read_text(encoding="utf-8")

    asyncio.run(scenario())


def test_busy_provider_stops_all_calls_without_logging_raw_body_or_retrying(tmp_path):
    path = tmp_path / "calls.json"
    calls = []

    async def scenario():
        async def respond(request):
            calls.append(request)
            return httpx.Response(
                429, json={"error": {"code": "1305", "message": "private-provider-body"}}
            )

        budget = BudgetTransport(path, 270, 110, transport=httpx.MockTransport(respond))
        async with httpx.AsyncClient(transport=budget) as client:
            await client.post(
                "https://provider.invalid/chat/completions", json={"model": "glm-5.3-flash"}
            )
            with pytest.raises(ModelError, match="EVALUATION_STOPPED"):
                await client.post(
                    "https://provider.invalid/embeddings", json={"model": "embedding-3"}
                )
        assert len(calls) == 1
        assert budget.state["calls"][0]["providerCode"] == "1305"
        assert "private-provider-body" not in path.read_text(encoding="utf-8")
        reloaded = BudgetTransport(path, 270, 110, transport=httpx.MockTransport(respond))
        with pytest.raises(ModelError, match="EVALUATION_STOPPED"):
            reloaded.reserve("model", "glm-5.3-flash")
        assert reloaded.state["used"] == {"model": 1, "embedding": 0}

    asyncio.run(scenario())


def test_ambiguous_reservation_survives_restart_and_never_resets_budget(tmp_path):
    path = tmp_path / "calls.json"
    first = BudgetTransport(path, 2, 1)
    first.reserve("model", "glm-5.3-flash")
    reloaded = BudgetTransport(path, 2, 1)
    assert reloaded.state["used"]["model"] == 1
    assert reloaded.state["stopped"] == "AMBIGUOUS_PROVIDER_CALL"
    with pytest.raises(ModelError, match="EVALUATION_STOPPED"):
        reloaded.reserve("model", "glm-5.3-flash")


def test_shared_budget_reloads_before_every_reservation_across_runs(tmp_path):
    if "run_id" not in inspect.signature(BudgetTransport).parameters:
        pytest.skip("shared-ledger run_id contract is awaiting the runner implementation")
    path = tmp_path / "shared-provider-calls.json"
    first = BudgetTransport(path, 2, 1, run_id="run-a")
    second = BudgetTransport(path, 2, 1, run_id="run-b")

    entry_a = first.reserve("model", "glm-5.3-flash")
    first.finish(entry_a, {"status": "completed", "usage": {"total_tokens": 10}})
    entry_b = second.reserve("model", "glm-5.3-flash")
    second.finish(entry_b, {"status": "completed", "usage": {"total_tokens": 12}})

    state = json.loads(path.read_text(encoding="utf-8"))
    assert state["used"] == {"model": 2, "embedding": 0}
    assert [call["runId"] for call in state["calls"]] == ["run-a", "run-b"]
    with pytest.raises(ModelError, match="EVALUATION_BUDGET_EXHAUSTED"):
        first.reserve("model", "glm-5.3-flash")


def test_shared_budget_propagates_fail_stop_to_an_already_open_run(tmp_path):
    if "run_id" not in inspect.signature(BudgetTransport).parameters:
        pytest.skip("shared-ledger fail-stop contract is awaiting the runner implementation")
    path = tmp_path / "shared-provider-calls.json"

    async def scenario():
        async def busy(_request):
            return httpx.Response(429, json={"error": {"code": "1305", "message": "private"}})

        failed = BudgetTransport(
            path, 2, 1, run_id="run-a", transport=httpx.MockTransport(busy)
        )
        already_open = BudgetTransport(path, 2, 1, run_id="run-b")
        async with httpx.AsyncClient(transport=failed) as client:
            await client.post(
                "https://provider.invalid/chat/completions", json={"model": "glm-5.3-flash"}
            )
        with pytest.raises(ModelError, match="EVALUATION_STOPPED"):
            already_open.reserve("embedding", "embedding-3")
        state = json.loads(path.read_text(encoding="utf-8"))
        assert state["stopped"] == "PROVIDER_REQUEST_FAILED"
        assert state["used"] == {"model": 1, "embedding": 0}
        assert "private" not in path.read_text(encoding="utf-8")

    asyncio.run(scenario())


def test_run_state_resumes_only_the_same_source_and_shared_ledger(tmp_path):
    path = tmp_path / "run-state.json"
    ledger = tmp_path / "provider-calls.json"
    state = RunState.create(
        path,
        schema="casepilot_eval_one",
        checkpoint_schema="casepilot_eval_one_cp",
        run_id="run-one",
        fingerprint="source-one",
        budget_ledger=ledger,
    )
    assert not state.is_complete("reports", "A01:1")
    state.begin("capabilities")
    state.complete("capabilities", {"status": "passed"})
    state.begin("reports", item="A01:1", data={"taskId": "task-one"})
    state.complete("reports", {"taskId": "task-one"}, item="A01:1")

    resumed = RunState.resume(path, fingerprint="source-one", budget_ledger=ledger)
    assert resumed.run_id == "run-one"
    assert resumed.schema == "casepilot_eval_one"
    assert resumed.checkpoint_schema == "casepilot_eval_one_cp"
    assert resumed.value("capabilities") == {"status": "passed"}
    assert resumed.value("reports", "A01:1") == {"taskId": "task-one"}
    with pytest.raises(RunStateError, match="EVALUATION_SOURCE_CHANGED"):
        RunState.resume(path, fingerprint="source-two", budget_ledger=ledger)
    with pytest.raises(RunStateError, match="EVALUATION_BUDGET_LEDGER_CHANGED"):
        RunState.resume(
            path,
            fingerprint="source-one",
            budget_ledger=tmp_path / "other-provider-calls.json",
        )


def test_run_state_refuses_to_guess_replay_for_an_unfinished_stage(tmp_path):
    path = tmp_path / "run-state.json"
    ledger = tmp_path / "provider-calls.json"
    state = RunState.create(
        path,
        schema="casepilot_eval_one",
        checkpoint_schema="casepilot_eval_one_cp",
        run_id="run-one",
        fingerprint="source-one",
        budget_ledger=ledger,
    )
    state.begin("reports", item="A01:1", data={"taskId": "task-one"})

    with pytest.raises(RunStateError, match="EVALUATION_STAGE_IN_PROGRESS"):
        RunState.resume(path, fingerprint="source-one", budget_ledger=ledger)


def test_source_manifest_fingerprint_covers_relevant_untracked_source(monkeypatch, tmp_path):
    monkeypatch.setattr(
        artifacts,
        "read_model_config",
        lambda: SimpleNamespace(
            api_key="must-never-be-recorded",
            chat_model="glm-5.3-flash",
            embedding_model="embedding-3",
            embedding_dimensions=1024,
            timeout_ms=30000,
        ),
    )
    monkeypatch.setattr(artifacts, "data_manifest", lambda: EXPECTED_DATA_HASHES)
    source = tmp_path / "apps/api/src"
    source.mkdir(parents=True)
    (source / "new_module.py").write_text("VALUE = 1\n", encoding="utf-8")

    first = artifacts.build_source_manifest(tmp_path)
    first_fingerprint = artifacts.source_fingerprint(first)
    (source / "new_module.py").write_text("VALUE = 2\n", encoding="utf-8")
    second = artifacts.build_source_manifest(tmp_path)

    assert first["trees"]["apps/api/src"] != second["trees"]["apps/api/src"]
    assert first_fingerprint != artifacts.source_fingerprint(second)
    assert first["data"] == EXPECTED_DATA_HASHES
    assert first["configuration"] == {
        "chatModel": "glm-5.3-flash",
        "embeddingModel": "embedding-3",
        "embeddingDimensions": 1024,
        "embeddingProfile": "zhipu:embedding-3:1024:v1",
        "promptVersion": artifacts.PROMPT_VERSION,
        "timeoutMs": 30000,
    }
    assert "must-never-be-recorded" not in json.dumps(first)


def test_manual_review_template_requires_all_reports_claims_browser_and_recovery_evidence():
    samples = load("reports.json")
    plan = [(sample, repetition) for repetition in range(1, 4) for sample in samples]
    review = artifacts.manual_review_template(plan)

    reports = review["semantic"]["reports"]
    assert [(row["sampleId"], row["repetition"]) for row in reports] == [
        (sample["id"], repetition) for repetition in range(1, 4) for sample in samples
    ]
    assert len(reports) == 30
    for row in reports:
        assert row["status"] == "pending"
        assert row["taskId"] is None and row["generationId"] is None
        assert row["reviewer"] == "" and row["reviewedAt"] is None
        assert row["sectionsIndependent"] == "pending"
        assert row["rulesPreserved"] == "pending"
        assert row["claims"]
        assert set(row["claims"][0]) == {
            "claim",
            "sectionKey",
            "citationIds",
            "sourceSupports",
            "limitationPreserved",
            "notes",
        }
    browser_ids = {item["id"] for item in review["browser"]["checks"]}
    assert {
        "review-approve",
        "review-reject",
        "section-incremental",
        "two-followups",
        "conversation-switch-isolation",
        "sse-reconnect",
        "citation-neighbour-bounds",
        "html-and-injection-output",
        "old-new-generation-citations",
    } <= browser_ids
    assert {item["id"] for item in review["recovery"]["checks"]} == {
        "provider-request-in-flight",
        "committed-section-not-repeated",
        "event-cursor-replay",
        "budget-not-reset",
    }


def test_report_plan_runs_a_breadth_first_pass_before_repetitions():
    samples = load("reports.json")
    plan = report_plan(samples)

    assert len(plan) == 30
    assert [(sample["id"], repetition) for sample, repetition in plan] == [
        (sample["id"], repetition) for repetition in range(1, 4) for sample in samples
    ]
    assert {
        sample["id"]: sum(candidate["id"] == sample["id"] for candidate, _ in plan)
        for sample in samples
    } == {sample["id"]: 3 for sample in samples}


def test_report_gate_requires_citations_scope_sections_and_three_completed_report_calls():
    corpus = load("corpus.json")
    sample = load("reports.json")[0]
    generation = "generation-one"
    task = {
        "status": "completed",
        "ruleFindings": [{"code": code} for code in sample["rules"]],
        "report": {"insufficientEvidence": False},
        "citations": [
            {
                "generationId": generation,
                "productCode": corpus["productCode"],
                "clauseVersion": corpus["clauseVersion"],
            }
        ],
        "sections": [
            {"sectionKey": "summary"},
            {"sectionKey": "findings"},
            {"sectionKey": "recommendations"},
        ],
    }
    audit = {
        "calls": [
            {
                "key": f"model:report:{section}:1",
                "kind": "model",
                "status": "completed",
            }
            for section in ("summary", "findings", "recommendations")
        ]
    }

    assert all(report_checks(sample, task, audit, generation, corpus).values())

    without_citations = {**task, "citations": []}
    assert report_checks(sample, without_citations, audit, generation, corpus)[
        "citationsPresentWhenExpected"
    ] is False

    wrong_scope = {
        **task,
        "citations": [{**task["citations"][0], "generationId": "other-generation"}],
    }
    assert report_checks(sample, wrong_scope, audit, generation, corpus)["scope"] is False

    incomplete_calls = {"calls": [{"key": "model:analysis:1", "status": "completed"}]}
    assert report_checks(sample, task, incomplete_calls, generation, corpus)[
        "callAuditComplete"
    ] is False


def test_report_gate_allows_no_citation_only_for_an_explicit_insufficient_sample():
    corpus = load("corpus.json")
    sample = next(item for item in load("reports.json") if item["insufficient"])
    task = {
        "status": "completed",
        "ruleFindings": [{"code": code} for code in sample["rules"]],
        "report": {"insufficientEvidence": True},
        "citations": [],
        "sections": [
            {"sectionKey": "summary"},
            {"sectionKey": "findings"},
            {"sectionKey": "recommendations"},
        ],
    }
    audit = {
        "calls": [
            {
                "key": f"model:report:{section}:1",
                "kind": "model",
                "status": "completed",
            }
            for section in ("summary", "findings", "recommendations")
        ]
    }

    checks = report_checks(sample, task, audit, "generation-one", corpus)
    assert checks["insufficientWhenRequired"] is True
    assert checks["citationsPresentWhenExpected"] is True

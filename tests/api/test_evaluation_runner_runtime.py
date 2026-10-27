"""Runner-only contracts that never start the API or contact the provider."""

import json
import sys
from types import SimpleNamespace

import pytest
from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import evaluate_v1
from evaluation.budget import BudgetLedger, BudgetReconciliationError


class _Response:
    status_code = 200

    def __init__(self, payload=None):
        self.payload = payload or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class _Process:
    def poll(self):
        return None

    def terminate(self):
        return None

    def wait(self, timeout):
        return 0


class _Client:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, path):
        assert path.startswith("/evaluation/retrieval/")
        return _Response({"status": "passed", "generationId": "generation-one"})


class _Ledger:
    def __init__(self, path, model_limit, embedding_limit, **kwargs):
        self.state = {
            "limits": {"model": model_limit, "embedding": embedding_limit},
            "used": {"model": 0, "embedding": 0},
            "migratedUsed": {"model": 0, "embedding": 0},
            "stopped": None,
        }

    def ensure_active(self):
        return None


def _ambiguous_ledger(call=None, *, stopped="PROVIDER_REQUEST_INTERRUPTED"):
    target = call or {
        "id": "14ef1270-32d0-4c66-91c0-fb6d8fb0935d",
        "runId": "run-capability-one",
        "kind": "model",
        "model": "glm-5.3-flash",
        "status": "ambiguous",
        "at": "2026-10-27T00:00:00+00:00",
        "errorType": "ConnectError",
        "durationMs": 42,
    }
    return {
        "version": 2,
        "limits": {"model": 270, "embedding": 110},
        "used": {"model": 3, "embedding": 0},
        "migratedUsed": {"model": 2, "embedding": 0},
        "stopped": stopped,
        "calls": [
            {
                "id": "historical-completed",
                "runId": "run-old",
                "kind": "model",
                "model": "glm-4.7-flash",
                "status": "completed",
            },
            target,
        ],
    }


def _task(*, citations):
    return {
        "status": "completed",
        "ruleFindings": [],
        "citations": citations,
        "sections": [
            {"sectionKey": "summary"},
            {"sectionKey": "findings"},
            {"sectionKey": "recommendations"},
        ],
        "report": {"insufficientEvidence": False},
    }


def _audit():
    return {
        "calls": [
            {"key": f"model:report:{section}:1", "status": "completed"}
            for section in ("summary", "findings", "recommendations")
        ]
    }


def test_no_live_flag_stops_before_creating_output_or_budget(tmp_path):
    output = tmp_path / "run"
    ledger = tmp_path / "shared.json"
    with pytest.raises(SystemExit, match="--live is required"):
        evaluate_v1.run(
            SimpleNamespace(live=False, output=output, budget_ledger=ledger)
        )
    assert not output.exists()
    assert not ledger.exists()


def test_operator_can_confirm_one_exact_ambiguous_call_as_consumed(tmp_path):
    path = tmp_path / "shared-ledger.json"
    before = _ambiguous_ledger()
    path.write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")
    ledger = BudgetLedger(path, 270, 110, require_existing=True)

    result = ledger.reconcile_ambiguous(
        call_id="14ef1270-32d0-4c66-91c0-fb6d8fb0935d",
        run_id="run-capability-one",
        kind="model",
        operator="acceptance-operator",
    )

    after = json.loads(path.read_text(encoding="utf-8"))
    assert result == {
        "outcome": "reconciled",
        "callId": "14ef1270-32d0-4c66-91c0-fb6d8fb0935d",
        "runId": "run-capability-one",
        "kind": "model",
        "used": {"model": 3, "embedding": 0},
        "stopped": None,
        "reconciliation": after["calls"][1]["reconciliation"],
    }
    assert after["used"] == before["used"]
    assert after["calls"][0] == before["calls"][0]
    assert after["calls"][1] == {
        **before["calls"][1],
        "status": "consumed",
        "reconciliation": {
            "action": "confirmed_consumed",
            "operator": "acceptance-operator",
            "at": after["calls"][1]["reconciliation"]["at"],
            "previousStatus": "ambiguous",
            "previousStop": "PROVIDER_REQUEST_INTERRUPTED",
        },
    }
    assert after["stopped"] is None

    reconciled_bytes = path.read_bytes()
    repeated = ledger.reconcile_ambiguous(
        call_id="14ef1270-32d0-4c66-91c0-fb6d8fb0935d",
        run_id="run-capability-one",
        kind="model",
        operator="acceptance-operator",
    )
    assert repeated["outcome"] == "already_reconciled"
    assert path.read_bytes() == reconciled_bytes


@pytest.mark.parametrize(
    ("change", "arguments", "error"),
    [
        (
            lambda state: None,
            {"call_id": "wrong-call"},
            "EVALUATION_RECONCILIATION_CALL_NOT_UNIQUE",
        ),
        (
            lambda state: None,
            {"run_id": "wrong-run"},
            "EVALUATION_RECONCILIATION_RUN_MISMATCH",
        ),
        (
            lambda state: None,
            {"kind": "embedding"},
            "EVALUATION_RECONCILIATION_KIND_MISMATCH",
        ),
        (
            lambda state: state["calls"][1].update(status="completed"),
            {},
            "EVALUATION_RECONCILIATION_STATUS_MISMATCH",
        ),
        (
            lambda state: state.update(stopped="PROVIDER_REQUEST_FAILED"),
            {},
            "EVALUATION_RECONCILIATION_STOP_MISMATCH",
        ),
        (
            lambda state: state["calls"].append(
                {
                    "id": "other-unresolved",
                    "runId": "run-two",
                    "kind": "embedding",
                    "status": "reserved",
                }
            ),
            {},
            "EVALUATION_RECONCILIATION_OTHER_UNRESOLVED",
        ),
    ],
)
def test_operator_reconciliation_rejects_every_non_exact_state_without_rewrite(
    tmp_path, change, arguments, error
):
    path = tmp_path / "shared-ledger.json"
    state = _ambiguous_ledger()
    change(state)
    path.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    original = path.read_bytes()
    ledger = BudgetLedger(path, 270, 110, require_existing=True)
    request = {
        "call_id": "14ef1270-32d0-4c66-91c0-fb6d8fb0935d",
        "run_id": "run-capability-one",
        "kind": "model",
        "operator": "acceptance-operator",
    }
    request.update(arguments)

    with pytest.raises(BudgetReconciliationError, match=error):
        ledger.reconcile_ambiguous(**request)
    assert path.read_bytes() == original


def test_reconciliation_requires_an_existing_shared_ledger(tmp_path):
    path = tmp_path / "missing.json"
    with pytest.raises(
        BudgetReconciliationError,
        match="EVALUATION_RECONCILIATION_LEDGER_NOT_FOUND",
    ):
        BudgetLedger(path, 270, 110, require_existing=True)
    assert not path.exists()


def test_first_shared_ledger_includes_historical_run_usage(tmp_path):
    historical = tmp_path / "docs" / "验收" / "old-run" / "provider-calls.json"
    historical.parent.mkdir(parents=True)
    historical.write_text(
        json.dumps(
            {
                "limits": {"model": 270, "embedding": 110},
                "used": {"model": 2, "embedding": 1},
                "stopped": None,
                "calls": [],
            }
        ),
        encoding="utf-8",
    )
    assert evaluate_v1.legacy_budget_usage(tmp_path, tmp_path / "shared.json") == {
        "model": 2,
        "embedding": 1,
    }


def test_new_run_initializes_separate_manual_browser_and_recovery_artifacts(tmp_path):
    output = tmp_path / "run"
    args = SimpleNamespace(
        output=output,
        resume=False,
        budget_ledger=tmp_path / "shared.json",
        model_limit=270,
        embedding_limit=110,
    )
    evaluate_v1._prepare_run(args, {"source": "fingerprint-input"}, [])

    manual = json.loads((output / "manual-review.json").read_text(encoding="utf-8"))
    browser = json.loads(
        (output / "browser" / "checklist.json").read_text(encoding="utf-8")
    )
    recovery = json.loads(
        (output / "recovery" / "results.json").read_text(encoding="utf-8")
    )

    assert set(manual) == {"version", "status", "semantic"}
    assert browser["status"] == "pending" and browser["checks"]
    assert recovery["status"] == "pending" and recovery["checks"]


def test_round_one_requires_complete_attributable_semantic_signoff():
    samples = [{"id": "A01"}, {"id": "A02"}]
    review = evaluate_v1.manual_review_template(
        evaluate_v1.report_plan(samples)
    )
    assert not evaluate_v1.round_one_semantic_review_passed(review, samples)

    for row in review["semantic"]["reports"]:
        if row["repetition"] != 1:
            continue
        row.update(
            status="passed",
            citationSupportsClaims="passed",
            insufficientEvidenceHandled="passed",
            promptInjectionResisted="passed",
            sectionsIndependent="passed",
            rulesPreserved="passed",
            reviewer="reviewer@example.test",
            reviewedAt="2026-10-27T12:00:00+08:00",
            claims=[
                {
                    "claim": "The saved source directly supports this conclusion.",
                    "sectionKey": "findings",
                    "citationIds": ["citation-1"],
                    "sourceSupports": "passed",
                    "limitationPreserved": "passed",
                    "notes": "",
                }
            ],
        )

    assert evaluate_v1.round_one_semantic_review_passed(review, samples)

    review["semantic"]["reports"][0]["reviewer"] = ""
    assert not evaluate_v1.round_one_semantic_review_passed(review, samples)


def test_report_plan_finishes_each_breadth_first_round_before_the_next():
    samples = [{"id": "A01"}, {"id": "A02"}]
    assert [(sample["id"], repetition) for sample, repetition in evaluate_v1.report_plan(samples)] == [
        ("A01", 1),
        ("A02", 1),
        ("A01", 2),
        ("A02", 2),
        ("A01", 3),
        ("A02", 3),
    ]


def test_stop_after_defaults_to_capability_and_bounds_report_work(tmp_path):
    args = evaluate_v1.build_parser().parse_args(["--live", "--output", str(tmp_path)])
    assert args.stop_after == "capability"

    plan = evaluate_v1.report_plan([{"id": "A01"}, {"id": "A02"}])
    assert evaluate_v1.reports_for_stop_after(plan, "capability") == []
    assert evaluate_v1.reports_for_stop_after(plan, "retrieval") == []
    assert [
        (sample["id"], repetition)
        for sample, repetition in evaluate_v1.reports_for_stop_after(
            plan, "round-one"
        )
    ] == [("A01", 1), ("A02", 1)]
    assert evaluate_v1.reports_for_stop_after(plan, "automated") == plan


@pytest.mark.parametrize(
    ("stop_after", "expected_publications", "expected_reports", "expected_reason"),
    [
        ("capability", 0, [], "STOP_AFTER_CAPABILITY"),
        ("retrieval", 3, [], "STOP_AFTER_RETRIEVAL"),
        (
            "round-one",
            3,
            [(f"A{index:02}", 1) for index in range(1, 11)],
            "ROUND_ONE_SEMANTIC_REVIEW_REQUIRED",
        ),
    ],
)
def test_staged_run_never_crosses_the_authorized_boundary(
    tmp_path,
    monkeypatch,
    stop_after,
    expected_publications,
    expected_reports,
    expected_reason,
):
    samples = [
        {
            "id": f"A{index:02}",
            "caseId": "case-one",
            "question": "Question",
            "rules": [],
            "insufficient": False,
        }
        for index in range(1, 11)
    ]
    corpus = {
        "pages": ["Page one"],
        "productCode": "AUTO",
        "clauseVersion": "2025",
    }
    output = tmp_path / stop_after
    publications = []
    reports = []
    original_read_json = evaluate_v1._read_json

    monkeypatch.setenv("DATABASE_URL", "postgresql://offline-test")
    monkeypatch.setattr(evaluate_v1, "load_environment", lambda: None)
    monkeypatch.setattr(
        evaluate_v1,
        "load",
        lambda name: samples if name == "reports.json" else corpus,
    )
    monkeypatch.setattr(
        evaluate_v1, "build_source_manifest", lambda root: {"source": "frozen"}
    )
    monkeypatch.setattr(evaluate_v1, "BudgetLedger", _Ledger)
    monkeypatch.setattr(evaluate_v1.subprocess, "Popen", lambda *args, **kwargs: _Process())
    monkeypatch.setattr(evaluate_v1.httpx, "get", lambda *args, **kwargs: _Response())
    monkeypatch.setattr(evaluate_v1.httpx, "Client", _Client)
    monkeypatch.setattr(
        evaluate_v1,
        "_read_json",
        lambda path: {"status": "passed"}
        if path.name == "capabilities.json"
        else original_read_json(path),
    )

    def fake_publication(state, client, *, item, **kwargs):
        publications.append(item)
        return "generation-one" if item == "original" else f"generation-{item}"

    def fake_report(state, client, sample, repetition, *args):
        reports.append((sample["id"], repetition))

    monkeypatch.setattr(evaluate_v1, "_ensure_publication", fake_publication)
    monkeypatch.setattr(evaluate_v1, "_run_report", fake_report)

    args = SimpleNamespace(
        live=True,
        resume=False,
        stop_after=stop_after,
        model_limit=270,
        embedding_limit=110,
        budget_ledger=tmp_path / "shared-ledger.json",
        output=output,
        keep_server=False,
    )
    assert evaluate_v1.run(args) == 0

    result = json.loads((output / "results.json").read_text(encoding="utf-8"))
    assert len(publications) == expected_publications
    assert reports == expected_reports
    assert result["reason"] == expected_reason
    assert result["providerStopped"] is None


def test_report_gate_requires_evidence_and_all_three_section_calls():
    sample = {"rules": [], "insufficient": False}
    corpus = {"productCode": "AUTO", "clauseVersion": "2025"}
    empty = evaluate_v1.report_checks(sample, _task(citations=[]), _audit(), "g1", corpus)
    assert empty["citationsPresentWhenExpected"] is False

    citation = {
        "generationId": "g1",
        "productCode": "AUTO",
        "clauseVersion": "2025",
    }
    missing_call = _audit()
    missing_call["calls"].pop()
    checked = evaluate_v1.report_checks(
        sample, _task(citations=[citation]), missing_call, "g1", corpus
    )
    assert checked["citationsPresentWhenExpected"] is True
    assert checked["callAuditComplete"] is False

    passed = evaluate_v1.report_checks(
        sample, _task(citations=[citation]), _audit(), "g1", corpus
    )
    assert all(passed.values())

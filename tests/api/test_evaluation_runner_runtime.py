"""Runner-only contracts that never start the API or contact the provider."""

import json
import sys
from types import SimpleNamespace

import pytest
from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import evaluate_v1


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

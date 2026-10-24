"""Pure V0 parity, not semantic retrieval or the full V1 rules matrix."""

from copy import deepcopy

from casepilot.cases.repository import get_case
from casepilot.cases.rules import evaluate_claim_rules
from casepilot.cases.seeds import CASES
from casepilot.knowledge.demo import search_clauses


def test_fixed_rule_order_and_source():
    result = evaluate_claim_rules(CASES[0])
    assert [finding["code"] for finding in result] == [
        "MISSING_REPAIR_INVOICE",
        "ACCIDENT_BEFORE_POLICY",
    ]
    assert all(finding["source"] == "rule" for finding in result)


def test_complete_case_has_no_findings():
    assert evaluate_claim_rules(CASES[1]) == []


def test_cross_material_date_conflict_retains_actual_dates():
    claim = deepcopy(CASES[1])
    claim["materials"][0]["fields"]["accidentDate"] = "2026-09-13"
    findings = evaluate_claim_rules(claim)
    assert [f["code"] for f in findings] == ["ACCIDENT_DATE_CONFLICT"]
    assert "2026-09-13" in findings[0]["detail"]
    assert "2026-09-12" in findings[0]["detail"]


def test_case_read_does_not_allow_mutating_shared_fixture():
    first = get_case(CASES[0]["id"])
    first["materials"][0]["fields"]["accidentDate"] = "changed"
    assert get_case(CASES[0]["id"])["materials"][0]["fields"]["accidentDate"] == "2026-08-08"
    assert get_case("missing") is None


def test_keyword_metadata_isolation_and_traceable_citations():
    finding = {
        "code": "MISSING_REPAIR_INVOICE",
        "severity": "medium",
        "title": "维修发票缺失",
        "detail": "材料缺失",
    }
    result = search_clauses("AUTO-COMPREHENSIVE", "2025-01", [finding])
    assert result[0]["id"] == "AUTO-2025-01-18"
    assert all("2024" not in c["id"] for c in result)
    assert all(c["title"] and c["content"] and c["score"] > 0 for c in result)
    assert search_clauses("OTHER-PRODUCT", "2025-01", [finding]) == []
    assert search_clauses("AUTO-COMPREHENSIVE", "missing", [finding]) == []


def test_clean_case_default_retrieval():
    assert [c["id"] for c in search_clauses("AUTO-COMPREHENSIVE", "2025-01", [])] == [
        "AUTO-2025-01-22"
    ]

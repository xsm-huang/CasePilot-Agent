"""Fact provenance, strengthened V1 rules and reference whitelist boundaries."""

from copy import deepcopy

import pytest
from agent_fixtures import assessment, clause
from casepilot.analyses.agent_errors import AgentError
from casepilot.analyses.evidence import case_facts, checked_assessment, merge_citations
from casepilot.cases.evidence_rules import evaluate_evidence_rules
from casepilot.cases.repository import get_case


def test_fact_ids_are_stable_and_missing_invoice_retains_directory_provenance():
    claim = get_case("CASE-2026-001")
    facts = case_facts(claim)
    assert facts == case_facts(deepcopy(claim))
    findings = evaluate_evidence_rules(claim, facts)
    assert [finding["code"] for finding in findings] == [
        "MISSING_REPAIR_INVOICE",
        "ACCIDENT_BEFORE_POLICY",
    ]
    assert findings[0]["factRefs"] == ["materials:types"]
    assert findings[1]["sourceValues"] == [
        {"factId": "case:accidentDate", "value": "2026-08-08"},
        {"factId": "case:policyEffectiveDate", "value": "2026-08-10"},
    ]


@pytest.mark.parametrize(
    "value,code",
    [
        (None, "DATE_MISSING"),
        ("", "DATE_MISSING"),
        ("2026-02-30", "DATE_INVALID"),
        ("2026-2-03", "DATE_INVALID"),
        (True, "DATE_INVALID"),
        (20260912, "DATE_INVALID"),
    ],
)
def test_missing_and_invalid_dates_are_distinct_and_never_compared_as_strings(value, code):
    claim = get_case("CASE-2026-002")
    claim["accidentDate"] = value
    findings = evaluate_evidence_rules(claim, case_facts(claim))
    finding = next(f for f in findings if f["code"] == code)
    assert finding["factRefs"] == ["case:accidentDate"]
    assert not any(f["code"] == "ACCIDENT_BEFORE_POLICY" for f in findings)


def test_materials_matching_each_other_but_conflicting_with_case_are_not_missed():
    claim = get_case("CASE-2026-002")
    claim["accidentDate"] = "2026-09-13"
    findings = evaluate_evidence_rules(claim, case_facts(claim))
    conflict = next(f for f in findings if f["code"] == "ACCIDENT_DATE_CONFLICT")
    assert set(conflict["factRefs"]) == {
        "case:accidentDate",
        "material:0:accidentDate",
        "material:1:accidentDate",
    }
    assert {entry["value"] for entry in conflict["sourceValues"]} == {"2026-09-12", "2026-09-13"}


def test_required_material_date_missing_and_optional_invoice_dates_are_distinguished():
    claim = get_case("CASE-2026-002")
    assert evaluate_evidence_rules(claim, case_facts(claim)) == []
    del claim["materials"][0]["fields"]["accidentDate"]
    findings = evaluate_evidence_rules(claim, case_facts(claim))
    assert len(findings) == 1
    assert findings[0]["code"] == "DATE_MISSING"
    assert findings[0]["factRefs"] == ["material:0:accidentDate"]


@pytest.mark.parametrize(
    "patch",
    [
        {"productCode": "OTHER"},
        {"clauseVersion": "old"},
        {"generationId": "another"},
        {"page": True},
        {"content": ""},
        {"fileName": None},
    ],
)
def test_wrong_scope_or_fabricated_source_metadata_is_rejected(patch):
    context = {
        "productCode": "AUTO-COMPREHENSIVE",
        "clauseVersion": "2025-01",
        "generationId": "generation-1",
    }
    with pytest.raises(AgentError):
        merge_citations([], [clause() | patch], context)


def test_citation_whitelist_strips_distance_and_rejects_unknown_ids_or_empty_support():
    context = {
        "productCode": "AUTO-COMPREHENSIVE",
        "clauseVersion": "2025-01",
        "generationId": "generation-1",
    }
    citations = merge_citations([], [clause()], context)
    assert "distance" not in citations[0]
    assert merge_citations(citations, [clause()], context) == citations
    facts = case_facts(get_case("CASE-2026-002"))
    assert checked_assessment(assessment(), facts, citations)["findings"]
    for output in [
        assessment(fact="other-case:fact"),
        assessment(citation="other-generation:chunk"),
        assessment(citation=None),
    ]:
        with pytest.raises(AgentError):
            checked_assessment(output, facts, citations)
    result = checked_assessment(assessment(citation=None, insufficient=True), facts, [])
    assert result["insufficientEvidence"] is True

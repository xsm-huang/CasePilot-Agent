from casepilot.analyses.evidence import case_facts
from casepilot.analyses.review_input import ReviewInputBuilder
from casepilot.cases.evidence_rules import evaluate_evidence_rules
from casepilot.cases.review_repository import get_review_case_input, review_input_version
from casepilot.schemas.review_cases import ClosedClaimReviewSnapshot, ReviewPreflight


class EmptyKnowledgeRepository:
    async def list_documents(self):
        return []


class EmptyKnowledge:
    repository = EmptyKnowledgeRepository()


async def test_preflight_allows_partial_review_and_fixes_input_snapshot():
    builder = ReviewInputBuilder(EmptyKnowledge())
    preflight, snapshot = await builder.build("C03")
    ReviewPreflight.model_validate(preflight)
    ClosedClaimReviewSnapshot.model_validate(snapshot)
    assert preflight["status"] == "partial"
    assert any(item["status"] == "executable" for item in preflight["scopeItems"])
    assert any(item["status"] == "limited" for item in preflight["scopeItems"])
    assert preflight["expectedInputVersion"] == review_input_version(
        {"case": snapshot["payload"], "knowledgeBindings": snapshot["knowledgeBindings"]}
    )
    assert all("relativePath" not in item for item in snapshot["payload"]["documents"])


async def test_missing_material_is_a_scoped_finding_not_a_blocker():
    _, snapshot = await ReviewInputBuilder(EmptyKnowledge()).build("C03")
    facts = case_facts(snapshot)
    findings = evaluate_evidence_rules(snapshot, facts)
    assert [item["code"] for item in findings] == ["DATA_GAP_GAP-C03-CALC"]
    assert findings[0]["factRefs"] == ["dataGaps:GAP-C03-CALC"]


def test_review_input_returns_defensive_copy():
    first = get_review_case_input("C01")
    first["claims"][0]["claimNumber"] = "changed"
    assert get_review_case_input("C01")["claims"][0]["claimNumber"] != "changed"

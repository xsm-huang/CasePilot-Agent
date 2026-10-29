"""Business gates, normal cases, per-finding history and immutable report versions."""

from copy import deepcopy
from uuid import uuid4

import pytest
from agent_fixtures import assessment
from casepilot.analyses.agent_errors import AgentError
from casepilot.analyses.checks import merge_checks, run_checks
from casepilot.analyses.evidence import checked_assessment
from casepilot.analyses.review import eligibility, new_review
from casepilot.cases.review_repository import get_review_case_input
from test_http_acceptance import decision
from workspace_fixtures import new_task, settle
from workspace_fixtures import workspace as workspace


@pytest.mark.parametrize("case_id", ["C01", "C02"])
def test_normal_case_arithmetic_payments_and_scope_do_not_create_issues(case_id):
    snapshot = {"payload": get_review_case_input(case_id)}
    checks = [
        r
        for node in ("archive", "coverage", "consistency", "amount")
        for r in run_checks(snapshot, node)
    ]
    assert checks and not [r for r in checks if r["status"] in {"issue", "limited"}]
    assert any(r["checkId"].startswith("payment:") for r in checks)


def test_payment_difference_and_missing_calculation_are_different_results():
    snapshot = {"payload": get_review_case_input("C03")}
    checks = run_checks(snapshot, "amount") + run_checks(snapshot, "consistency")
    assert [
        (r["status"], r["nodeKey"]) for r in checks if r["checkId"] == "payment:CLM-C03-COM-TP"
    ] == [("issue", "amount")]
    assert [(r["status"], r["nodeKey"]) for r in checks if r["checkId"] == "gap:GAP-C03-CALC"] == [
        ("limited", "amount")
    ]


def test_unrelated_clause_cannot_resolve_a_missing_calculation():
    state = new_review({"payload": get_review_case_input("C03")}, "test")
    task = dict(
        reviewState=state,
        reviewHistory=[],
        status="waiting_review",
        context={"inputVersion": "fixed", "knowledgeBindings": []},
        caseSnapshot={},
        facts=[],
        citations=[],
        evidenceSupplements=[],
    )
    assert not eligibility(task)["allowed"]
    assert any("必要检查未完成" in b for b in eligibility(task)["blockers"])


def test_model_repeats_enrich_one_original_finding_without_double_counting():
    original = {
        "checkId": "payment:C03",
        "status": "issue",
        "nodeKey": "amount",
        "source": "rule",
        "title": "支付差额",
        "detail": "审批8000，实付9000",
        "factRefs": ["approvals:a", "payments:p"],
        "citationRefs": [],
    }
    model = original | {
        "checkId": "ai:extra",
        "source": "ai",
        "detail": "原文显示无退款或其他审批",
        "factRefs": ["approvals:a", "payments:p", "material_pages:doc:1"],
    }
    merged = merge_checks([original], [model], {"findings": []})
    assert len(merged) == 1
    assert merged[0]["checkId"] == "payment:C03"
    assert merged[0]["sources"] == ["rule", "ai"]
    assert "原文显示无退款" in merged[0]["detail"]
    assert original["detail"] == "审批8000，实付9000"


def test_existing_evidence_identifier_resolves_to_its_canonical_fact_reference():
    value = assessment(fact="EV-C03-CALC-GAP", citation="clause-1")
    facts = [{"factId": "evidence:EV-C03-CALC-GAP"}]
    result = checked_assessment(value, facts, [{"citationId": "clause-1", "content": "支持原文"}])
    assert result["findings"][0]["factRefs"] == ["evidence:EV-C03-CALC-GAP"]


def test_material_identifiers_cannot_be_mislabelled_as_contract_clauses():
    value = assessment(citation=None)
    value["findings"] = []
    value["checkedItems"] = value["checkedItems"][:1]
    value["checkedItems"][0].update(factRefs=[], citationRefs=["evidence:EV-DOC-1"])
    result = checked_assessment(value, [{"factId": "evidence:EV-DOC-1"}], [])
    assert result["checkedItems"][0]["factRefs"] == ["evidence:EV-DOC-1"]
    assert result["checkedItems"][0]["citationRefs"] == []
    value["checkedItems"][0]["citationRefs"] = ["evidence:another-case"]
    with pytest.raises(AgentError, match="ANALYSIS_REFERENCE_INVALID"):
        checked_assessment(value, [{"factId": "evidence:EV-DOC-1"}], [])


@pytest.mark.database
@pytest.mark.parametrize("case_id", ["C01", "C02"])
def test_normal_case_requires_human_coverage_confirmation_and_has_concise_report(
    workspace, case_id
):
    client, _, _ = workspace
    _, created = new_task(client, case_id)
    task = settle(client, created["id"], "waiting_review")
    assert task["report"]["kind"] == "pending_review"
    assert not [r for r in task["checks"] if r["status"] in {"issue", "limited"}]
    assert "findings" not in [s["sectionKey"] for s in task["sections"]]
    assert "recommendations" not in [s["sectionKey"] for s in task["sections"]]
    body = {
        "decision": "approve",
        "comment": "已检查本次范围、事实和报告",
        "expectedRevision": task["revision"],
        "interruptKey": task["pendingReview"]["interruptKey"],
    }
    path = f"/api/analyses/{task['id']}/review"
    assert (
        client.post(path, json=body, headers={"Idempotency-Key": str(uuid4())}).status_code == 400
    )
    pending_report = deepcopy(task["report"])
    assert decision(client, task).status_code == 202
    final = settle(client, task["id"], "completed")
    assert final["report"]["kind"] == "final"
    assert final["report"]["operatorId"] == "test-reviewer"
    assert final["reports"][0] == pending_report
    assert final["report"]["version"] == 2
    accepted = next(e for e in final["execution"]["timeline"] if e["type"] == "review.accepted")
    assert accepted["data"]["comment"] and accepted["data"]["operatorId"] == "test-reviewer"
    assert client.get("/api/analyses", params={"caseId": case_id}).json()
    assert all(
        t["caseId"] == case_id
        for t in client.get("/api/analyses", params={"caseId": case_id}).json()
    )


@pytest.mark.database
def test_finding_review_is_idempotent_versioned_and_cannot_bypass_an_unresolved_check(workspace):
    client, _, _ = workspace
    _, created = new_task(client, "C03")
    task = settle(client, created["id"], "waiting_review")
    snapshot = deepcopy(task["caseSnapshot"])
    original_report = deepcopy(task["report"])
    assert decision(client, task).status_code == 409
    item = next(c for c in task["reviewState"]["findings"] if c["status"] == "issue")
    viewed = client.post(
        f"/api/analyses/{task['id']}/evidence-views",
        json={
            "expectedRevision": task["revision"],
            "nodeKey": "amount",
            "comment": "查看支付及核赔原始记录",
            "factRefs": item["factRefs"],
        },
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert viewed.status_code == 202, viewed.text
    task = client.get(f"/api/analyses/{task['id']}").json()
    body = {
        "decision": "confirmed",
        "comment": "已核对核赔及有效支付，存在未解释的差额",
        "expectedRevision": task["revision"],
        "factRefs": item["factRefs"],
        "followup": "交支付经办岗位核查差额及纠正记录",
        "findingVersion": item["version"],
        "evidenceViewed": True,
    }
    path = f"/api/analyses/{task['id']}/findings/{item['findingId']}/review"
    key = str(uuid4())
    bad = client.post(
        path,
        json=body | {"factRefs": ["other-task-fact"]},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert bad.status_code == 400
    first = client.post(path, json=body, headers={"Idempotency-Key": key})
    assert first.status_code == 202, first.text
    assert client.post(path, json=body, headers={"Idempotency-Key": key}).json() == first.json()
    assert (
        client.post(path, json=body, headers={"Idempotency-Key": str(uuid4())}).status_code == 409
    )
    updated = client.get(f"/api/analyses/{task['id']}").json()
    assert len(updated["reviewHistory"]) == 1
    assert updated["reviewHistory"][0]["nodeKey"] == "amount"
    assert updated["caseSnapshot"] == snapshot
    assert updated["reports"][0] == original_report
    assert updated["report"]["kind"] == "stage"
    assert decision(client, updated).status_code == 409
    change = body | {
        "expectedRevision": updated["revision"],
        "decision": "pending",
        "comment": "发现还需核实是否存在关联审批",
        "followup": "请支付经办调取关联审批",
        "recipient": "支付经办岗位",
        "missingItems": "关联审批记录",
        "previousReviewId": updated["reviewHistory"][-1]["reviewId"],
    }
    assert (
        client.post(path, json=change, headers={"Idempotency-Key": str(uuid4())}).status_code == 400
    )
    change["changeReason"] = "新增记录线索，原结论需进一步核实"
    assert (
        client.post(path, json=change, headers={"Idempotency-Key": str(uuid4())}).status_code == 202
    )
    final = client.get(f"/api/analyses/{task['id']}").json()
    assert len(final["reviewHistory"]) == 2
    assert final["reviewHistory"][0]["decision"] == "confirmed"
    assert final["reviewHistory"][1]["decision"] == "pending"
    assert len([e for e in final["execution"]["timeline"] if e["type"] == "finding.reviewed"]) == 2


@pytest.mark.database
def test_unidentified_operator_cannot_complete_review(workspace, monkeypatch):
    client, _, _ = workspace
    _, created = new_task(client, "C01")
    task = settle(client, created["id"], "waiting_review")
    monkeypatch.delenv("CASEPILOT_OPERATOR_ID", raising=False)
    assert decision(client, task).status_code == 400

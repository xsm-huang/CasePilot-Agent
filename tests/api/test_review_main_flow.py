"""Actual PostgreSQL acceptance of coverage, recovery and all three approved changes."""

from copy import deepcopy
from uuid import uuid4

import pytest
from conftest import ROOT
from test_http_acceptance import decision
from workspace_fixtures import new_task, settle
from workspace_fixtures import workspace as workspace

pytestmark = pytest.mark.database


def read(client, task):
    return client.get(f"/api/analyses/{task['id']}").json()


def write(client, task, action, **body):
    payload = {
        "expectedRevision": task["revision"],
        "nodeKey": "amount",
        "comment": "已核对实际资料，追加本次操作及其依据",
        **body,
    }
    if action == "findings":
        payload.pop("comment")
    response = client.post(
        f"/api/analyses/{task['id']}/{action}",
        json=payload,
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 202, response.text
    return read(client, task)


def review(client, task, finding, value, **extra):
    task = write(
        client, task, "evidence-views", factRefs=finding["factRefs"], **extra.get("view", {})
    )
    previous = [r for r in task["reviewHistory"] if r["findingId"] == finding["findingId"]]
    body = dict(
        expectedRevision=task["revision"],
        decision=value,
        comment="已查看原始记录并核对本项的实际处理依据",
        factRefs=finding["factRefs"],
        followup="请支付经办岗位保留核查及后续办理记录",
        findingVersion=finding["version"],
        previousReviewId=previous[-1]["reviewId"] if previous else "",
        evidenceViewed=True,
        changeReason="依据补充记录重新核实本项" if previous else "",
    )
    body.update({k: v for k, v in extra.items() if k != "view"})
    response = client.post(
        f"/api/analyses/{task['id']}/findings/{finding['findingId']}/review",
        json=body,
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 202, response.text
    return read(client, task)


def test_manual_completion_final_revision_and_immutable_reports(workspace):
    client, _, chat = workspace
    _, created = new_task(client, "C03")
    task = settle(client, created["id"], "waiting_review")
    original_input = deepcopy(task["caseSnapshot"])
    first_report = deepcopy(task["report"])
    assert len(task["reviewState"]["businessNodes"]) == 6
    assert all(
        e["data"]["parentNodeRunId"]
        for e in task["execution"]["timeline"]
        if e["type"] == "tool.started"
    )
    gap = next(f for f in task["reviewState"]["findings"] if f["checkId"].startswith("gap:"))
    payment = next(
        f for f in task["reviewState"]["findings"] if f["checkId"].startswith("payment:")
    )
    task = review(client, task, payment, "confirmed")
    task = review(client, task, gap, "excluded")
    # A decision does not make the missing calculation executed.
    assert not task["finalizationEligibility"]["allowed"]
    assert decision(client, task).status_code == 409
    source = ROOT / "test-data/claims-review/v1/supplements/C03/补充计算书_第三方商业险_演示.pdf"
    response = client.post(
        f"/api/analyses/{task['id']}/supplements",
        data={
            "title": "补充商业三者计算书",
            "expectedRevision": task["revision"],
            "materialType": "calculation",
            "entityIds": '["CLM-C03-COM-TP"]',
        },
        files={"file": (source.name, source.read_bytes(), "application/pdf")},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 201, response.text
    supplement = response.json()
    task = read(client, task)
    task = write(client, task, "evidence-views", supplementIds=[supplement["supplementId"]])
    task = write(
        client,
        task,
        "human-completions",
        targetId=gap["checkId"],
        supplementIds=[supplement["supplementId"]],
        steps="对照补充计算书逐项核算",
        result="核算结果与计算书相符",
        inputsFen=[800000],
        operation="sum",
        resultFen=800000,
    )
    assert task["finalizationEligibility"]["allowed"], task["finalizationEligibility"]
    assert (
        next(n for n in task["reviewState"]["businessNodes"] if n["nodeKey"] == "amount")["status"]
        == "unable"
    )
    assert decision(client, task).status_code == 202
    task = settle(client, task["id"], "completed")
    final = deepcopy(task["report"])
    before_calls = len(chat.calls)
    task = write(
        client,
        task,
        "followup-records",
        targetId=payment["findingId"],
        recipient="支付核查岗位",
        state="following",
        source="经办人员业务记录 #001",
        result="已受理核查，尚未办结",
    )
    assert task["status"] == "completed" and task["report"]["kind"] == "final"
    assert task["reports"][final["version"] - 1] == final
    task = write(client, task, "reopen-review", comment="发现新的业务记录，需要再次核实审查结论")
    assert task["status"] == "waiting_review" and task["reviewState"]["reviewCycleId"] == 2
    task = review(
        client,
        task,
        payment,
        "pending",
        recipient="支付核查岗位",
        missingItems="需补充其他审批记录",
    )
    assert decision(client, task).status_code == 409
    task = review(client, task, payment, "confirmed")
    assert decision(client, task).status_code == 202
    task = settle(client, task["id"], "completed")
    assert len(chat.calls) == before_calls
    assert task["caseSnapshot"] == original_input
    assert task["reports"][0] == first_report
    assert task["reports"][final["version"] - 1] == final
    assert task["report"]["statistics"]["confirmed"] == 1


def test_explicit_scope_adjustment_does_not_mark_unable_check_passed(workspace):
    client, _, _ = workspace
    _, created = new_task(client, "C03")
    task = settle(client, created["id"], "waiting_review")
    payment = next(
        f for f in task["reviewState"]["findings"] if f["checkId"].startswith("payment:")
    )
    task = review(client, task, payment, "confirmed")
    task = write(
        client,
        task,
        "scope-adjustments",
        state="exclude",
        checkIds=["gap:GAP-C03-CALC"],
        result="本次仅完成取得的审批及支付资料核对，不对缺失计算书的理算正确性出具结论",
    )
    assert task["finalizationEligibility"]["allowed"]
    assert decision(client, task).status_code == 202
    final = settle(client, task["id"], "completed")
    assert "调整后" in final["report"]["conclusion"]
    assert final["report"]["statistics"]["outside_adjusted_scope"] == 1
    assert (
        next(c for c in final["checks"] if c["checkId"] == "gap:GAP-C03-CALC")["status"]
        == "limited"
    )


def test_failed_model_keeps_partial_results_and_explicit_recovery_deduplicates(workspace):
    client, _, chat = workspace
    chat.fail_phase = "clauses"
    _, created = new_task(client, "C01")
    task = settle(client, created["id"], "waiting_review")
    nodes = {n["nodeKey"]: n for n in task["reviewState"]["businessNodes"]}
    assert nodes["clauses"]["status"] == "failed"
    assert nodes["amount"]["status"] == "completed"
    assert task["checks"] and task["report"]["kind"] == "stage"
    assert not task["finalizationEligibility"]["allowed"]
    original = deepcopy(task["report"])
    response = client.post(
        f"/api/analyses/{task['id']}/recover",
        json={"expectedRevision": task["revision"]},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 202, response.text
    recovered = settle(client, task["id"], "waiting_review")
    assert recovered["finalizationEligibility"]["allowed"], recovered["finalizationEligibility"]
    assert len(recovered["checks"]) == len({r["checkId"] for r in recovered["checks"]})
    assert recovered["reports"][0] == original
    assert recovered["reviewState"]["nodeHistory"]


def test_manual_finding_requires_viewed_evidence_and_rejects_stale_decisions(
    workspace, monkeypatch
):
    client, app, _ = workspace
    _, created = new_task(client, "C01")
    task = settle(client, created["id"], "waiting_review")
    task = write(
        client,
        task,
        "findings",
        title="人工补充核查事项",
        detail="经人工查看原记录，发现需要进一步核实的事项",
        entityIds=["CLM-C01-OWN"],
        factRefs=["case:accident"],
        recommendation="交审查人员逐条核实",
    )
    item = next(f for f in task["reviewState"]["findings"] if f["source"] == "human")
    assert not task["finalizationEligibility"]["allowed"]
    body = dict(
        expectedRevision=task["revision"],
        findingVersion=item["version"],
        decision="excluded",
        comment="已查看原材料，有合理依据可排除此疑点",
        factRefs=["case:accident"],
        evidenceViewed=True,
    )
    path = f"/api/analyses/{task['id']}/findings/{item['findingId']}/review"
    assert (
        client.post(path, json=body, headers={"Idempotency-Key": str(uuid4())}).json()["code"]
        == "EVIDENCE_NOT_VIEWED"
    )
    task = review(client, task, item, "excluded")
    assert task["finalizationEligibility"]["allowed"]
    assert (
        client.post(path, json=body, headers={"Idempotency-Key": str(uuid4())}).status_code == 409
    )
    task = review(client, task, item, "referred", recipient="专业核查岗位")
    task = write(
        client,
        task,
        "professional-records",
        targetId=item["findingId"],
        recipient="专业核查岗位",
        state="following",
        result="已登记材料，等待专业意见",
    )
    assert not task["finalizationEligibility"]["allowed"]
    request_body = dict(
        expectedRevision=task["revision"],
        nodeKey="amount",
        targetId=item["findingId"],
        comment="录入已取得的专业核查意见",
        recipient="专业核查岗位",
        state="opinion_received",
        source="专业人员签署记录 #002",
        result="经专业核查，本项线索不成立",
    )
    endpoint = f"/api/analyses/{task['id']}/professional-records"
    assert (
        client.post(
            endpoint, json=request_body, headers={"Idempotency-Key": str(uuid4())}
        ).status_code
        == 409
    )
    monkeypatch.setenv("CASEPILOT_PROFESSIONAL_RECORDERS", "test-reviewer")
    task = write(
        client,
        task,
        "professional-records",
        **{k: v for k, v in request_body.items() if k != "expectedRevision"},
    )
    task = review(client, task, item, "excluded")
    assert task["finalizationEligibility"]["allowed"]
    stale = app.state.store.get(task["id"])
    task = write(client, task, "evidence-views", factRefs=["case:accident"])

    async def reject_stale_snapshot():
        from casepilot.analyses.errors import AnalysisError

        with pytest.raises(AnalysisError, match="任务版本或事件游标"):
            await app.state.store.repository.save(stale)

    client.portal.call(reject_stale_snapshot)

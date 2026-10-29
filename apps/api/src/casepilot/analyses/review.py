"""Shared coverage, findings and report-basis rules; no UI-derived decisions."""

import hashlib
import json
from copy import deepcopy

from ..schemas.review import Finding
from .checks import NODE_NAMES, run_checks


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def new_review(snapshot, task_id):
    plan = []
    for key in ("archive", "coverage", "consistency", "amount"):
        for item in run_checks(snapshot, key):
            plan.append(plan_item(item))
    for key, title in (
        ("consistency", "材料原文一致性"),
        ("clauses", "条款与原处理依据"),
        ("amount", "金额口径及支付解释核对"),
    ):
        plan.append(
            dict(checkId=f"{key}:assessment", nodeKey=key, title=title, required=True, entityIds=[])
        )
    return dict(
        reviewModelVersion=1,
        checkPlan=list({r["checkId"]: r for r in plan}.values()),
        checks=[],
        findings=[],
        records=[],
        findingHistory=[],
        reviewCycleId=1,
        nodeHistory=[],
        businessNodes=[
            dict(
                nodeRunId=f"{task_id}:{key}:1",
                nodeKey=key,
                attempt=1,
                status="not_started",
                startedAt=None,
                endedAt=None,
                durationMs=0,
                summary="尚未执行",
                reason="",
            )
            for key in NODE_NAMES
        ],
    )


def plan_item(item):
    return dict(
        checkId=item["checkId"],
        nodeKey=item["nodeKey"],
        title=item["title"],
        required=item["status"] not in {"not_applicable", "out_of_scope"},
        entityIds=item.get("entityIds", []),
    )


def enrich(item, task):
    item = deepcopy(item)
    by_id = {f["factId"]: f["value"] for f in task["facts"]}
    values = {ref: by_id[ref] for ref in item.get("factRefs", []) if ref in by_id}
    entities, policies, coverages = set(item.get("entityIds", [])), set(), set()
    for value in values.values():
        if isinstance(value, dict):
            for key in ("entityIds", "claimIds", "targetClaimIds"):
                entities.update(v for v in value.get(key, []) if isinstance(v, str))
            for key in ("claimId", "vehicleId", "partyId", "lossId"):
                if value.get(key):
                    entities.add(value[key])
            if value.get("policyId"):
                policies.add(value["policyId"])
            if value.get("coverageId"):
                coverages.add(value["coverageId"])
    case = task["caseSnapshot"]["payload"]
    related = [a for a in case.get("approvals", []) if a["claimId"] in entities]
    policies.update(a["policyId"] for a in related if a.get("policyId"))
    coverages.update(a["coverageId"] for a in related if a.get("coverageId"))
    for policy in case.get("policies", []):
        if any(c["coverageId"] in coverages for c in policy.get("coverages", [])):
            policies.add(policy["policyId"])
    item.update(
        entityIds=sorted(entities),
        policyIds=sorted(policies),
        coverageIds=sorted(coverages),
        originalValues=item.get("originalValues") or values,
    )
    item.setdefault("uncertainty", "待人员核实" if item["status"] != "passed" else "")
    item.setdefault(
        "recommendation", "查看原始依据并核实本项" if item["status"] != "passed" else ""
    )
    item.setdefault(
        "statements",
        [
            dict(
                source=item["source"],
                detail=item["detail"],
                factRefs=item.get("factRefs", []),
                citationRefs=item.get("citationRefs", []),
            )
        ],
    )
    return item


def commit_checks(task, checks):
    state = task["reviewState"]
    results = {r["checkId"]: r for r in state["checks"]}
    findings = {f["findingId"]: f for f in state["findings"]}
    plan = {p["checkId"]: p for p in state["checkPlan"]}
    for row in checks:
        row = enrich(row, task)
        results[row["checkId"]] = row
        plan.setdefault(row["checkId"], plan_item(row))
        if row["status"] in {"issue", "limited", "out_of_scope"}:
            fid = f"finding:{row['checkId']}"
            previous = findings.get(fid)
            value = Finding.model_validate(
                row
                | dict(
                    findingId=fid,
                    version=previous["version"] if previous else 1,
                    kind={
                        "issue": "issue",
                        "limited": "limitation",
                        "out_of_scope": "out_of_scope",
                    }[row["status"]],
                )
            ).model_dump()
            if previous and previous != value:
                state["findingHistory"].append(deepcopy(previous))
                value["version"] += 1
            findings[fid] = value
        else:
            fid = f"finding:{row['checkId']}"
            if fid in findings and findings[fid]["active"]:
                state["findingHistory"].append(deepcopy(findings[fid]))
                findings[fid].update(active=False, version=findings[fid]["version"] + 1)
    state.update(
        checks=list(results.values()),
        findings=list(findings.values()),
        checkPlan=list(plan.values()),
    )
    task["checks"] = deepcopy(state["checks"])


def excluded_checks(task):
    excluded = set()
    for row in task["reviewState"]["records"]:
        if row["kind"] == "scope_adjustment":
            if row["state"] == "restore":
                excluded.difference_update(row["checkIds"])
            else:
                excluded.update(row["checkIds"])
    return excluded


def latest_reviews(task):
    return {row["findingId"]: row for row in task["reviewHistory"]}


def unresolved_findings(task):
    reviews, excluded = latest_reviews(task), excluded_checks(task)
    return [
        f
        for f in task["reviewState"]["findings"]
        if f["active"]
        and f["kind"] != "out_of_scope"
        and f["checkId"] not in excluded
        and (
            f["findingId"] not in reviews
            or reviews[f["findingId"]]["findingVersion"] != f["version"]
            or reviews[f["findingId"]]["decision"] not in {"confirmed", "excluded"}
        )
    ]


def report_basis(task):
    state = deepcopy(task["reviewState"])
    state["records"] = [r for r in state["records"] if r["kind"] != "evidence_view"]
    return dict(
        inputVersion=task["context"]["inputVersion"],
        knowledgeBindings=deepcopy(task["context"]["knowledgeBindings"]),
        caseSnapshot=deepcopy(task["caseSnapshot"]),
        reviewState=state,
        reviewHistory=deepcopy(task["reviewHistory"]),
        facts=deepcopy(task["facts"]),
        citations=deepcopy(task["citations"]),
        evidenceSupplements=deepcopy(task["evidenceSupplements"]),
    )


def eligibility(task):
    state = task["reviewState"]
    excluded = excluded_checks(task)
    completed = {r["targetId"] for r in state["records"] if r["kind"] == "human_completion"}
    checks = {c["checkId"]: c for c in state["checks"]}
    nodes = {n["nodeKey"]: n for n in state["businessNodes"]}
    blockers = []
    required = [p for p in state["checkPlan"] if p["required"] and p["checkId"] not in excluded]
    if not required:
        blockers.append("有效车损审查范围为空")
    for plan in required:
        key = plan["checkId"]
        if key in completed:
            continue
        item = checks.get(key)
        if not item or item["status"] == "limited":
            blockers.append(f"{NODE_NAMES[plan['nodeKey']]} / {plan['title']}：必要检查未完成")
        elif nodes[plan["nodeKey"]]["status"] in {"failed", "running", "not_started"}:
            blockers.append(f"{NODE_NAMES[plan['nodeKey']]}：自动执行尚未有效完成")
    for finding in unresolved_findings(task):
        blockers.append(f"{finding['title']}：尚无有效的最终人工结论")
    if nodes["report"]["status"] != "completed":
        blockers.append("发现与报告汇总尚未完成")
    if task["status"] in {"queued", "running"}:
        blockers.append("自动执行或恢复尚在进行")
    return dict(
        allowed=not blockers,
        blockers=list(dict.fromkeys(blockers)),
        basisHash=digest(report_basis(task)),
    )


def review_status(task):
    if task["status"] == "completed":
        return "completed"
    if unresolved_findings(task):
        reviews = latest_reviews(task)
        if any(r["decision"] in {"pending", "referred"} for r in reviews.values()):
            return "pending_verification"
    return "reviewing" if task["reviewHistory"] else "pending_review"


def statistics(task):
    reviews = latest_reviews(task)
    counts = {
        key: 0
        for key in (
            "pending_review",
            "confirmed",
            "excluded",
            "pending",
            "referred",
            "out_of_scope",
            "outside_adjusted_scope",
        )
    }
    excluded = excluded_checks(task)
    for finding in task["reviewState"]["findings"]:
        if not finding["active"]:
            continue
        if finding["kind"] == "out_of_scope":
            counts["out_of_scope"] += 1
        elif finding["checkId"] in excluded:
            counts["outside_adjusted_scope"] += 1
        else:
            review = reviews.get(finding["findingId"])
            key = (
                review["decision"]
                if review and review["findingVersion"] == finding["version"]
                else "pending_review"
            )
            counts[key] += 1
    return counts

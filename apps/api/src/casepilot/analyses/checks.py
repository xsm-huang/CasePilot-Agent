"""Deterministic, scoped review checks. A restriction is never a business error."""

import hashlib
from copy import deepcopy
from datetime import datetime

from ..cases.review_repository import _sum_approved, _sum_paid

NODE_NAMES = {
    "archive": "档案整理与范围识别",
    "coverage": "保单与承保险种核验",
    "consistency": "材料一致性核对",
    "clauses": "条款检索与依据核对",
    "amount": "金额与支付核对",
    "report": "发现与报告汇总",
}


def check(check_id, node, status, title, detail, refs=(), citations=(), source="rule"):
    return dict(
        checkId=check_id,
        nodeKey=node,
        status=status,
        source=source,
        title=title,
        detail=detail,
        factRefs=list(refs),
        citationRefs=list(citations),
    )


def amount(value):
    return value.get("amountFen") if value and value.get("status") == "known" else None


def run_checks(snapshot, node):
    case = snapshot["payload"]
    rows = []
    targets = set(case["reviewScope"]["targetClaimIds"])
    if node == "archive":
        rows.append(
            check(
                "scope",
                node,
                "passed",
                "审查范围已固定",
                "目标赔案：" + "、".join(sorted(targets)),
                ["case:reviewScope"],
            )
        )
        injury = case.get("injury", {})
        status = injury.get("declaredStatus", "unknown")
        rows.append(
            check(
                "injury",
                node,
                "out_of_scope"
                if status == "injury_reported"
                else "limited"
                if status in {"unknown", "conflicting_information"}
                else "passed",
                "人伤范围识别",
                "原档案记录未报人伤；不等同于已完成全案人伤审查。"
                if status == "no_injury_reported"
                else "人伤线索需专业核实；车损共用事实受影响时保持未决。",
                ["case:injury"],
            )
        )
        if "third_party_vehicle" not in case["reviewScope"].get("lossTypes", []):
            rows.append(
                check(
                    "third_party_na",
                    node,
                    "not_applicable",
                    "第三方损失检查不适用",
                    "本次范围不涉及第三方损失，不作为缺件或未投保。",
                    ["case:reviewScope"],
                )
            )
    elif node == "coverage":
        accident = datetime.fromisoformat(case["accident"]["occurredAt"])
        for policy in case.get("policies", []):
            ref = f"policies:{policy['policyId']}"
            available = policy["availability"] == "available"
            start, end = policy.get("effectiveFrom"), policy.get("effectiveTo")
            if not available or not start or not end:
                state, detail = "limited", "保单或保险期间未取得，无法完成承保核验。"
            else:
                inside = datetime.fromisoformat(start) <= accident <= datetime.fromisoformat(end)
                state = "passed" if inside else "issue"
                detail = f"事故时间 {case['accident']['occurredAt']}；保险期间 {start} 至 {end}。"
            rows.append(
                check(
                    f"policy:{policy['policyId']}",
                    node,
                    state,
                    "保险期间核对",
                    detail,
                    [ref, "case:accident"],
                )
            )
        coverages = {
            c["coverageId"]: c for p in case.get("policies", []) for c in p.get("coverages", [])
        }
        for claim in case.get("claims", []):
            if claim["claimId"] not in targets:
                continue
            ids = claim.get("coverageIds", []) or (
                [claim["coverageId"]] if claim.get("coverageId") else []
            )
            # Some source records bind the coverage through calculations/approvals.
            if not ids:
                ids = sorted(
                    {
                        a["coverageId"]
                        for a in case.get("approvals", [])
                        if a["claimId"] == claim["claimId"]
                    }
                )
            known = bool(ids) and all(i in coverages for i in ids)
            insured = known and all(coverages[i]["status"] == "insured" for i in ids)
            rows.append(
                check(
                    f"coverage:{claim['claimId']}",
                    node,
                    "passed" if insured else "issue" if known else "limited",
                    "目标赔案承保险种核对",
                    f"{claim['claimId']}：" + "、".join(ids),
                    [f"claims:{claim['claimId']}"],
                )
            )
        for endorsement in case.get("endorsements", []):
            rows.append(
                check(
                    f"endorsement:{endorsement['endorsementId']}",
                    node,
                    "limited",
                    "批单与特别约定影响待确认",
                    "请结合批单原文、生效时间及对应损失核实影响。",
                    [f"endorsements:{endorsement['endorsementId']}"],
                )
            )
    elif node == "consistency":
        for gap in case.get("dataGaps", []):
            rows.append(
                check(
                    f"gap:{gap['gapId']}",
                    "amount" if "calculations" in gap.get("fieldPaths", []) else node,
                    "limited",
                    "本次档案未取得必要资料",
                    gap["description"],
                    [f"dataGaps:{gap['gapId']}"],
                )
            )
        observations = case.get("observations", [])
        for i, observation in enumerate(observations):
            rows.append(
                check(
                    f"observation:{i}",
                    node,
                    "limited",
                    "跨来源记录待核实",
                    str(observation),
                    [f"observations:{i}"],
                )
            )
        rows.append(
            check(
                "material_provenance",
                node,
                "passed",
                "材料版本与来源已核对",
                "已取得材料读取时校验固定 hash；逐页原文交由模型与结构化记录核对。",
                [
                    f"documents:{d['documentId']}"
                    for d in case.get("documents", [])
                    if d["status"] == "available"
                ],
            )
        )
    elif node == "amount":
        for calculation in case.get("calculations", []):
            if calculation["claimId"] not in targets:
                continue
            refs = [f"calculations:{calculation['calculationId']}"]
            for line in calculation.get("lines", []):
                values = [amount(v["amount"]) for v in line.get("inputs", [])]
                op = line["operation"]
                result = None
                if values and all(v is not None for v in values):
                    if op == "sum":
                        result = sum(values)
                    elif op == "difference" and len(values) == 2:
                        result = values[0] - values[1]
                    elif (
                        op == "recorded_formula"
                        and line.get("formulaText", "").replace(" ", "")
                        == "min(" + ",".join(map(str, values)) + ")"
                    ):
                        result = min(values)
                recorded = amount(line.get("result"))
                state = (
                    "limited"
                    if result is None or recorded is None
                    else "passed"
                    if result == recorded
                    else "issue"
                )
                rows.append(
                    check(
                        f"formula:{line['lineId']}",
                        node,
                        state,
                        "赔款算式核对",
                        f"{line['description']}：{line.get('formulaText')}；原记录 {recorded} 分，核算 {result} 分。",
                        refs,
                    )
                )
            lines = [amount(line.get("result")) for line in calculation.get("lines", [])]
            total = amount(calculation.get("totalAmount"))
            if lines and all(v is not None for v in lines) and total is not None:
                rows.append(
                    check(
                        f"total:{calculation['calculationId']}",
                        node,
                        "passed" if sum(lines) == total else "issue",
                        "计算书汇总核对",
                        f"明细合计 {sum(lines)} 分；记录总额 {total} 分。"
                        + calculation.get("adjustmentReason", ""),
                        refs,
                    )
                )
        for claim_id in sorted(targets):
            approved = _sum_approved(case, {claim_id})
            paid = _sum_paid(case, {claim_id})
            a, p = amount(approved), amount(paid)
            rows.append(
                check(
                    f"payment:{claim_id}",
                    node,
                    "limited" if a is None or p is None else "passed" if a == p else "issue",
                    "核赔与有效实付核对",
                    f"{claim_id}：核赔 {a} 分；有效实付 {p} 分；"
                    + (
                        f"差额 {p - a} 分，需核实其他审批、退款、冲销及无效付款。"
                        if a is not None and p is not None and a != p
                        else "按交易状态及退款、冲销关系计算。"
                    ),
                    [f"claims:{claim_id}"]
                    + [
                        f"approvals:{a['approvalId']}"
                        for a in case.get("approvals", [])
                        if a["claimId"] == claim_id
                    ]
                    + [
                        f"payments:{p['paymentId']}"
                        for p in case.get("payments", [])
                        if p["claimId"] == claim_id
                    ],
                )
            )
        seen = {}
        approvals = {a["approvalId"]: a for a in case.get("approvals", [])}
        for payment in case.get("payments", []):
            if payment["claimId"] not in targets or payment["status"] != "succeeded":
                continue
            ref = f"payments:{payment['paymentId']}"
            allocation = payment.get("approvalAllocations", [])
            values = [amount(a["amount"]) for a in allocation]
            valid = bool(allocation) and all(
                a["approvalId"] in approvals
                and approvals[a["approvalId"]]["claimId"] == payment["claimId"]
                for a in allocation
            )
            total = sum(values) if values and all(v is not None for v in values) else None
            rows.append(
                check(
                    f"allocation:{payment['paymentId']}",
                    node,
                    "passed" if valid and total == amount(payment["amount"]) else "limited",
                    "分笔支付与审批分配核对",
                    f"原交易 {payment['paymentId']}；审批分配合计 {total} 分；付款 {amount(payment['amount'])} 分；收款对象 {payment.get('payeePartyId')}。",
                    [ref] + [f"approvals:{a['approvalId']}" for a in allocation],
                )
            )
            transaction = payment.get("externalTransactionId")
            if transaction and transaction in seen:
                rows.append(
                    check(
                        f"duplicate:{transaction}",
                        node,
                        "issue",
                        "同一外部交易重复记录线索",
                        "相同外部交易编号出现多个有效记录，需核实是否重复入账及冲销关系，不直接认定重复赔付。",
                        [ref, seen[transaction]],
                    )
                )
            seen[transaction] = ref
    return rows


def material_scope_checks(facts):
    """Recognize positive injury evidence without treating an empty declaration as proof."""
    import re

    refs = [
        f["factId"]
        for f in facts
        if f["sourceType"] == "material"
        and isinstance(f["value"], str)
        and re.search(
            r"(?:有人受伤|人员受伤[：:]?有|伤者[：:]|诊断[：:]|医疗费用[：:]\s*[1-9])", f["value"]
        )
    ]
    if not refs:
        return []
    return [
        check(
            "injury:material",
            "archive",
            "out_of_scope",
            "材料中识别人伤线索",
            "原始材料出现伤者、诊断或医疗费用线索。请记录专业转交；如影响车损共用事实，须另行核实。",
            refs,
        )
    ]


def assessment_checks(assessment, snapshot, citations):
    rows = []
    category = {
        "issue": "issue",
        "limitation": "limited",
        "out_of_scope": "out_of_scope",
        "passed": "passed",
    }
    for item in [*assessment["findings"], *assessment.get("checkedItems", [])]:
        identity = hashlib.sha256(
            (
                item.get("issueCode", "evidence_review")
                + "|"
                + item["nodeKey"]
                + "|"
                + item["category"]
                + "|"
                + "|".join(sorted(item["factRefs"]))
            ).encode()
        ).hexdigest()[:16]
        rows.append(
            check(
                f"ai:{identity}",
                item["nodeKey"],
                category[item["category"]],
                item["title"],
                item["inference"]
                + (
                    "\n判断限制：" + "；".join(item["pendingItems"])
                    if item["evidenceStatus"] == "insufficient" and item["pendingItems"]
                    else ""
                ),
                item["factRefs"],
                item["citationRefs"],
                "ai",
            )
        )
    for binding in snapshot.get("knowledgeBindings", []):
        matches = [c for c in citations if c["generationId"] == binding.get("generationId")]
        rows.append(
            check(
                f"terms:{binding['documentId']}",
                "clauses",
                "passed" if binding["status"] == "ready" and matches else "limited",
                "固定版本条款检索",
                f"{binding['documentId']} · {binding['version']}："
                + (
                    f"已取得 {len(matches)} 个原文片段，具体责任判断仍须逐项核对。"
                    if matches
                    else "未取得对应版本条款原文，相关判断受限。"
                ),
                citations=[c["citationId"] for c in matches],
            )
        )
    for node, title in (
        ("consistency", "材料原文一致性审查"),
        ("clauses", "合同责任与处理依据审查"),
    ):
        if not any(item["nodeKey"] == node for item in assessment.get("checkedItems", [])):
            rows.append(
                check(
                    f"ai:coverage:{node}",
                    node,
                    "limited",
                    title + "未完成",
                    "本次模型没有返回该项检查及其依据，不能仅因检索成功或没有疑点就视为通过。",
                    source="ai",
                )
            )
    if assessment["insufficientEvidence"] and not any(r["status"] == "limited" for r in rows):
        rows.append(
            check(
                "ai:insufficient",
                "clauses",
                "limited",
                "部分判断依据不足",
                "；".join(assessment.get("pendingItems", []))
                or "模型未能完成全部依据核对，需人工核实。",
                source="ai",
            )
        )
    return rows


def merge_checks(deterministic, model_rows, assessment):
    """Keep one review per check while retaining additional model evidence verbatim."""
    rows = deepcopy(deterministic)
    related = {}
    for item in [*assessment["findings"], *assessment.get("checkedItems", [])]:
        identity = hashlib.sha256(
            (
                item.get("issueCode", "evidence_review")
                + "|"
                + item["nodeKey"]
                + "|"
                + item["category"]
                + "|"
                + "|".join(sorted(item["factRefs"]))
            ).encode()
        ).hexdigest()[:16]
        if item.get("relatedCheckId"):
            related[f"ai:{identity}"] = item["relatedCheckId"]
    for item in model_rows:
        refs = set(item["factRefs"])
        match = next(
            (
                r
                for r in rows
                if r["checkId"] == related.get(item["checkId"]) and r["status"] == item["status"]
            ),
            None,
        )
        if match is None and item["status"] in {"issue", "limited"}:
            for row in rows:
                common = set(row["factRefs"]) & refs
                gap = row["checkId"].startswith("gap:") and any(
                    r.startswith("dataGaps:") for r in common
                )
                payment = (
                    row["checkId"].startswith("payment:")
                    and any(r.startswith("payments:") for r in common)
                    and any(r.startswith("approvals:") for r in common)
                )
                if row["status"] == item["status"] and (gap or payment):
                    match = row
                    break
        if match is None:
            rows.append(item)
            continue
        if not match.get("statements"):
            match["statements"] = [
                dict(
                    source=match["source"],
                    detail=match["detail"],
                    factRefs=list(match["factRefs"]),
                    citationRefs=list(match["citationRefs"]),
                )
            ]
        match["statements"].append(
            dict(
                source=item["source"],
                detail=item["detail"],
                factRefs=list(item["factRefs"]),
                citationRefs=list(item["citationRefs"]),
            )
        )
        match["detail"] += "\nAI 补充核对：" + item["detail"]
        match["sources"] = list(
            dict.fromkeys([match["source"], *match.get("sources", []), item["source"]])
        )
        for field in ("factRefs", "citationRefs"):
            match[field] = list(dict.fromkeys([*match[field], *item[field]]))
    return rows

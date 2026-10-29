"""Render actual results and freeze each report's evidence and decisions."""

from .checks import NODE_NAMES
from .review import (
    digest,
    eligibility,
    latest_reviews,
    report_basis,
    statistics,
    unresolved_findings,
)

DECISIONS = {
    "confirmed": "确认问题",
    "excluded": "排除疑点",
    "pending": "待补充核实",
    "referred": "转专业复核",
}
STATES = {
    "passed": "检查通过",
    "issue": "业务疑点",
    "limited": "无法确认",
    "not_applicable": "不适用",
    "out_of_scope": "范围外",
}
NODE_STATES = {
    "not_started": "未开始",
    "running": "执行中",
    "completed": "已完成",
    "failed": "执行失败",
    "unable": "无法执行",
    "not_applicable": "不适用",
}
LABELS = {
    "paid_closed": "赔付结案",
    "refused_closed": "拒赔结案",
    "zero_closed": "零赔付结案",
    "other_closed": "其他结案",
    "settled": "已完成支付",
    "partial": "部分支付",
    "pending": "待处理",
    "failed": "失败",
    "not_applicable": "不适用",
    "unknown": "未知",
    "ready": "已取得固定版本",
    "unavailable": "未取得",
    "OWN_DAMAGE": "机动车损失保险",
    "THIRD_PARTY": "机动车第三者责任保险",
    "CTPL": "交强险",
    "human_completion": "人工补做检查",
    "scope_adjustment": "调整审查范围",
    "professional": "专业复核",
    "followup": "后续办理",
    "business_record": "补充业务记录",
    "reopen": "重新打开复核",
    "completed": "已完成",
    "exclude": "排除本次范围",
    "restore": "恢复本次范围",
    "opinion_received": "已收到专业意见",
    "transferred": "已转交",
    "in_progress": "办理中",
}


def label(value):
    return LABELS.get(value, value)


def unresolved_checks(task):
    return unresolved_findings(task)


def build_report(task, at, *, final=False):
    case, state = task["caseSnapshot"]["payload"], task["reviewState"]
    stats, reviews = statistics(task), latest_reviews(task)
    blockers = eligibility(task)["blockers"]
    adjusted = any(r["kind"] == "scope_adjustment" for r in state["records"])
    scope = "调整后所列车损范围" if adjusted else "所列车损范围和资料"
    if final:
        conclusion = (
            f"在{scope}内存在已确认问题" if stats["confirmed"] else f"在{scope}内未发现疑点"
        )
    elif blockers:
        conclusion = f"本次审查尚未完成，仍有 {len(blockers)} 项必要检查或人工事项待处理"
    else:
        conclusion = f"在{scope}内未发现未决疑点，待人工确认检查覆盖及报告内容"
    sections = []

    def add(key, text, rows=()):
        if not text:
            return
        for start in range(0, len(text), 6000):
            sections.append(
                dict(
                    sectionKey=key,
                    content=text[start : start + 6000],
                    committedAt=at,
                    factRefs=sorted({ref for r in rows for ref in r.get("factRefs", [])}),
                    citationRefs=sorted({ref for r in rows for ref in r.get("citationRefs", [])}),
                )
            )

    terms = "；".join(
        f"{b['documentId']} · {b['version']} · {label(b['status'])}"
        for b in task["context"]["knowledgeBindings"]
    )
    approvals = [
        a for a in case["approvals"] if a["claimId"] in case["reviewScope"]["targetClaimIds"]
    ]
    policy_ids = {a["policyId"] for a in approvals}
    coverage_ids = {a["coverageId"] for a in approvals}
    policies = "；".join(
        (p.get("policyNumber") or p["policyId"])
        + " / "
        + "、".join(
            label(c["coverageCode"]) for c in p["coverages"] if c["coverageId"] in coverage_ids
        )
        for p in case["policies"]
        if p["policyId"] in policy_ids
    )
    add(
        "summary",
        f"{conclusion}。\n目标赔案：{'、'.join(case['reviewScope']['targetClaimIds'])}。\n"
        f"关联报案：{'、'.join(dict.fromkeys(c['reportNumber'] for c in case['claims'] if c['claimId'] in case['reviewScope']['targetClaimIds']))}；事故时间：{case['accident']['occurredAt']}。\n"
        f"原结案/支付：{'；'.join(c['claimNumber'] + ' / ' + label(c['closureType']) + ' / ' + label(c['originalPaymentStatus']) for c in case['claims'] if c['claimId'] in case['reviewScope']['targetClaimIds'])}。\n"
        f"本次保单与险种：{policies}。\n"
        f"固定输入：{task['context']['inputVersion']}；材料 {len(case.get('documents', []))} 份。\n适用条款：{terms}。",
    )
    coverage = []
    for node in state["businessNodes"]:
        coverage.append(
            f"{NODE_NAMES[node['nodeKey']]}：{NODE_STATES[node['status']]}，{node['durationMs']} ms；{node['summary']}"
            + (f"；{node['reason']}" if node["reason"] else "")
        )
    coverage.extend(
        f"{r['title']}：{STATES[r['status']]}；{r['detail']}"
        for r in state["checks"]
        if r["status"] == "not_applicable"
    )
    add("coverage", "\n".join(coverage), state["checks"])
    findings = [f for f in state["findings"] if f["active"]]
    if findings:
        add(
            "findings",
            "\n".join(
                f"{f['findingId']} · {f['title']}：{f['detail']}；"
                + (
                    DECISIONS[reviews[f["findingId"]]["decision"]]
                    if f["findingId"] in reviews
                    and reviews[f["findingId"]]["findingVersion"] == f["version"]
                    else "待复核"
                )
                for f in findings
                if f["kind"] == "issue"
            ),
            findings,
        )
        add(
            "summary",
            "处理汇总："
            + "；".join(
                f"{name} {stats[key]} 项"
                for key, name in (
                    ("confirmed", "确认问题"),
                    ("excluded", "排除疑点"),
                    ("pending_review", "待复核"),
                    ("pending", "待核实"),
                    ("referred", "专业未完成"),
                    ("out_of_scope", "范围外"),
                    ("outside_adjusted_scope", "调整后未纳入"),
                )
            ),
        )
    limits = [f for f in findings if f["kind"] in {"limitation", "out_of_scope"}]
    add(
        "limitations",
        "\n".join(
            [f"{f['title']}：{f['detail']}" for f in limits]
            + case["reviewScope"].get("scopeLimitations", [])
            + blockers
        ),
        limits,
    )
    add(
        "reviews",
        "\n".join(
            f"{r['operatorId']} · {r['at']} · {r['findingId']} · {DECISIONS[r['decision']]}：{r['comment']}；{r['followup']}"
            for r in task["reviewHistory"]
        ),
        task["reviewHistory"],
    )
    records = [r for r in state["records"] if r["kind"] != "evidence_view"]
    add(
        "recommendations",
        "\n".join(
            f"{label(r['kind'])} · {r['operatorId']} · {r['at']}：{r['comment']}；{r['steps']}；{r['result']}；{r['recipient']}；{label(r['state'])}；来源 {r['source']}"
            for r in records
        ),
        records,
    )
    review = task.get("_review", {})
    if final:
        add(
            "reviews",
            f"本轮最终确认：{review.get('operatorId', '')} · {review.get('at', at)}\n{review.get('comment', '')}",
        )
    basis = report_basis(task)
    previous = task.get("report")
    return dict(
        caseId=task["caseId"],
        analysisId=task["id"],
        inputVersion=task["context"]["inputVersion"],
        generatedAt=at,
        kind="final"
        if final
        else "stage"
        if task["status"] in {"failed", "recoverable"}
        or task["evidenceSupplements"]
        or records
        or task["reviewHistory"]
        or any(n["status"] == "failed" for n in state["businessNodes"])
        else "pending_review",
        version=len(task["reports"]) + 1,
        operatorId=review.get("operatorId") if final else None,
        conclusion=conclusion,
        sections=sections,
        insufficientEvidence=bool(blockers),
        reviewerComment=review.get("comment") if final else None,
        basisHash=digest(basis),
        snapshot=basis,
        statistics=stats,
        revisionReason=records[-1]["comment"] if records else "自动分析结果汇总",
        replacesVersion=previous["version"] if previous else None,
    )

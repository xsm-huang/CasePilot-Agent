"""Pure V0 template report rendering; no model calls."""


def build_report(state):
    claim = state["claim"]
    findings = state["findings"]
    recommendation = (
        "建议暂缓赔付，优先核验事故发生时间与保险责任起期。"
        if any(f["code"] == "ACCIDENT_BEFORE_POLICY" for f in findings)
        else "建议补齐材料后复核赔付金额。"
        if findings
        else "未发现规则层面的显著疑点，可进入常规核赔。"
    )
    report = {
        "caseId": state["caseId"],
        "summary": f"{claim['claimant']}就车辆损失申请理赔 {claim['claimAmount']:,} 元，共提交 {len(claim['materials'])} 份材料。",
        "findings": findings,
        "recommendation": recommendation,
        "citations": state["citations"],
    }
    if state.get("review"):
        report["reviewerComment"] = state["review"]["comment"]
    return report

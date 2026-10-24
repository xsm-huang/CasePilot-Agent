"""Pure deterministic material and date rules."""


def evaluate_claim_rules(claim: dict) -> list[dict]:
    findings = []

    def add(code, severity, title, detail):
        findings.append(
            dict(code=code, source="rule", severity=severity, title=title, detail=detail)
        )

    if "repair_invoice" not in {m["type"] for m in claim["materials"]}:
        add(
            "MISSING_REPAIR_INVOICE",
            "medium",
            "维修发票缺失",
            "当前材料目录中未发现维修发票，无法核验实际修复费用。",
        )
    if claim["accidentDate"] < claim["policyEffectiveDate"]:
        add(
            "ACCIDENT_BEFORE_POLICY",
            "high",
            "事故早于保单生效",
            f"事故日期 {claim['accidentDate']} 早于保单生效日期 {claim['policyEffectiveDate']}。",
        )
    dates = list(
        dict.fromkeys(
            m["fields"]["accidentDate"]
            for m in claim["materials"]
            if isinstance(m["fields"].get("accidentDate"), str)
        )
    )
    if len(dates) > 1:
        add(
            "ACCIDENT_DATE_CONFLICT",
            "high",
            "跨材料事故日期冲突",
            f"材料中出现多个事故日期：{'、'.join(dates)}。",
        )
    return findings

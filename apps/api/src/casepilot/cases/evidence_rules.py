"""V1 rules validate dates and retain precise fact/source references."""

from datetime import date


def evaluate_evidence_rules(claim, facts):
    by_id = {fact["factId"]: fact for fact in facts}
    findings = []

    def add(code, severity, title, detail, refs):
        findings.append(
            {
                "code": code,
                "source": "rule",
                "severity": severity,
                "title": title,
                "detail": detail,
                "factRefs": refs,
                "sourceValues": [{"factId": ref, "value": by_id[ref]["value"]} for ref in refs],
            }
        )

    if not any(material.get("type") == "repair_invoice" for material in claim.get("materials", [])):
        add(
            "MISSING_REPAIR_INVOICE",
            "medium",
            "维修发票缺失",
            "当前材料目录中未发现维修发票。",
            ["materials:types"],
        )
    dates = {}
    for fact in facts:
        if fact["fieldPath"] not in {"accidentDate", "policyEffectiveDate"} and not fact[
            "fieldPath"
        ].endswith(".accidentDate"):
            continue
        value = fact["value"]
        if value is None or value == "":
            add(
                "DATE_MISSING",
                "high",
                "日期缺失",
                f"{fact['fieldPath']} 缺少日期，需核查来源。",
                [fact["factId"]],
            )
            continue
        try:
            if not isinstance(value, str) or len(value) != 10:
                raise ValueError()
            parsed = date.fromisoformat(value)
            if parsed.isoformat() != value:
                raise ValueError()
            dates[fact["factId"]] = parsed
        except ValueError:
            add(
                "DATE_INVALID",
                "high",
                "日期无效",
                f"{fact['fieldPath']} 不是有效的 YYYY-MM-DD 日期。",
                [fact["factId"]],
            )
    accident, effective = dates.get("case:accidentDate"), dates.get("case:policyEffectiveDate")
    if accident and effective and accident < effective:
        add(
            "ACCIDENT_BEFORE_POLICY",
            "high",
            "事故早于保单生效",
            "案件事故日期早于保单生效日期。",
            ["case:accidentDate", "case:policyEffectiveDate"],
        )
    accident_refs = [
        ref for ref in dates if ref == "case:accidentDate" or ref.startswith("material:")
    ]
    if len({dates[ref] for ref in accident_refs}) > 1:
        add(
            "ACCIDENT_DATE_CONFLICT",
            "high",
            "跨来源事故日期冲突",
            "案件与材料中的事故日期存在不同值，不自动选定任一来源为真。",
            accident_refs,
        )
    return findings

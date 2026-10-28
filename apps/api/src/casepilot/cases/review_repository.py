"""Read prepared review cases without exposing expected answers or review scripts."""

import hashlib
import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote

from ..config import PROJECT_ROOT

DEFAULT_REVIEW_CASES_DIR = PROJECT_ROOT / "test-data" / "claims-review" / "v1" / "inputs"


class ReviewCaseDataError(RuntimeError):
    pass


def review_cases_dir() -> Path:
    import os

    configured = os.getenv("CASEPILOT_REVIEW_CASES_DIR")
    return Path(configured).resolve() if configured else DEFAULT_REVIEW_CASES_DIR.resolve()


def _load_all() -> list[tuple[Path, dict[str, Any]]]:
    root = review_cases_dir()
    if not root.is_dir():
        return []
    loaded = []
    for path in sorted(root.glob("*/case.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ReviewCaseDataError(f"无法读取案件数据：{path.parent.name}") from error
        if value.get("datasetCaseId") != path.parent.name:
            raise ReviewCaseDataError(f"案件目录与编号不一致：{path.parent.name}")
        loaded.append((path.parent.resolve(), value))
    return loaded


def _money(value: dict[str, Any] | None, *, reason: str = "当前记录未提供该金额") -> dict:
    if not value:
        return {"status": "unknown", "amountFen": None, "currency": "CNY", "reason": reason}
    return {
        "status": value["status"],
        "amountFen": value.get("amountFen"),
        "currency": value.get("currency", "CNY"),
        "reason": value.get("reason"),
    }


def _sum_approved(case: dict[str, Any], target_ids: set[str]) -> dict:
    amounts = [
        approval.get("approvedAmount")
        for approval in case.get("approvals", [])
        if approval.get("claimId") in target_ids and approval.get("status") == "approved"
    ]
    if not amounts:
        return _money(None, reason="目标赔案没有已批准的核赔金额记录")
    if any(amount.get("status") != "known" for amount in amounts):
        return _money(None, reason="目标赔案存在未知核赔金额")
    return {
        "status": "known",
        "amountFen": sum(amount["amountFen"] for amount in amounts),
        "currency": "CNY",
        "reason": None,
    }


def _sum_paid(case: dict[str, Any], target_ids: set[str]) -> dict:
    payments = case.get("payments", [])
    by_id = {payment["paymentId"]: payment for payment in payments}

    def sign(payment: dict[str, Any], visiting: set[str]) -> int:
        payment_id = payment["paymentId"]
        if payment_id in visiting:
            raise ReviewCaseDataError(f"支付记录存在循环引用：{payment_id}")
        kind = payment.get("kind")
        if kind == "disbursement":
            return 1
        original_id = payment.get("originalPaymentId")
        original = by_id.get(original_id)
        if original is None:
            raise ReviewCaseDataError(f"支付更正缺少原交易：{payment_id}")
        if kind == "refund":
            return -1
        if kind == "reversal":
            return -sign(original, visiting | {payment_id})
        raise ReviewCaseDataError(f"未知支付类型：{kind}")

    effective = [
        payment
        for payment in payments
        if payment.get("claimId") in target_ids and payment.get("status") == "succeeded"
    ]
    if not effective:
        return _money(None, reason="目标赔案没有有效支付记录")
    if any(payment.get("amount", {}).get("status") != "known" for payment in effective):
        return _money(None, reason="目标赔案存在金额未知的有效支付记录")
    return {
        "status": "known",
        "amountFen": sum(sign(payment, set()) * payment["amount"]["amountFen"] for payment in effective),
        "currency": "CNY",
        "reason": None,
    }


def _claim(claim: dict[str, Any], role: str) -> dict:
    return {
        "claimId": claim["claimId"],
        "claimNumber": claim["claimNumber"],
        "reportNumber": claim["reportNumber"],
        "scopeRole": role,
        "closureType": claim["closureType"],
        "closedAt": claim["closedAt"],
        "originalPaymentStatus": claim["originalPaymentStatus"],
    }


def _summary(case: dict[str, Any]) -> dict:
    target_order = case["reviewScope"]["targetClaimIds"]
    related_order = case["reviewScope"]["relatedClaimIds"]
    target_ids = set(target_order)
    claims = {claim["claimId"]: claim for claim in case["claims"]}
    return {
        "id": case["datasetCaseId"],
        "revision": case["caseRevision"],
        "targetClaims": [_claim(claims[claim_id], "target") for claim_id in target_order],
        "relatedClaims": [_claim(claims[claim_id], "related") for claim_id in related_order],
        "vehicles": [
            {"vehicleId": item["vehicleId"], "role": item["role"], "plateNumber": item["plateNumber"]}
            for item in case["vehicles"]
        ],
        "accidentAt": case["accident"]["occurredAt"],
        "originalApprovedAmount": _sum_approved(case, target_ids),
        "effectivePaidAmount": _sum_paid(case, target_ids),
        "injuryStatus": case["injury"]["declaredStatus"],
        "latestReviewStatus": "not_started",
    }


def list_review_cases(
    *,
    query_type: str | None = None,
    query: str | None = None,
    closed_from: date | None = None,
    closed_to: date | None = None,
    injury_status: str | None = None,
    review_status: str | None = None,
) -> dict:
    loaded = _load_all()
    if not loaded:
        return {"dataStatus": "not_imported", "items": []}
    needle = query.strip().casefold() if query else None
    items = []
    for _, case in loaded:
        summary = _summary(case)
        all_claims = summary["targetClaims"] + summary["relatedClaims"]
        if needle:
            candidates = {
                "claim_number": [claim["claimNumber"] for claim in all_claims],
                "report_number": [claim["reportNumber"] for claim in all_claims],
                "plate_number": [vehicle["plateNumber"] for vehicle in summary["vehicles"]],
            }[query_type]
            if not any(needle in value.casefold() for value in candidates):
                continue
        closed_dates = [date.fromisoformat(claim["closedAt"][:10]) for claim in summary["targetClaims"]]
        if not any(
            (closed_from is None or value >= closed_from)
            and (closed_to is None or value <= closed_to)
            for value in closed_dates
        ):
            continue
        if injury_status and summary["injuryStatus"] != injury_status:
            continue
        if review_status and summary["latestReviewStatus"] != review_status:
            continue
        items.append(summary)
    items.sort(
        key=lambda item: (max(claim["closedAt"] for claim in item["targetClaims"]), item["id"]),
        reverse=True,
    )
    return {"dataStatus": "ready", "items": items}


def _source_resolver(case: dict[str, Any]):
    evidence = {item["evidenceId"]: item for item in case["evidence"]}
    documents = {item["documentId"]: item for item in case["documents"]}

    def resolve(refs: list[str] | None) -> list[dict]:
        result = []
        for ref in refs or []:
            item = evidence.get(ref)
            if item is None:
                raise ReviewCaseDataError(f"证据引用不存在：{ref}")
            document = documents.get(item.get("documentId"))
            result.append(
                {
                    "evidenceId": ref,
                    "sourceType": item["sourceType"],
                    "title": document["title"] if document else item.get("documentId") or "结构化业务记录",
                    "documentId": item.get("documentId"),
                    "documentVersion": item.get("documentVersion"),
                    "page": item.get("page"),
                    "recordPointer": item.get("recordPointer"),
                    "quote": item.get("quote"),
                }
            )
        return result

    return resolve


def _detail(case: dict[str, Any]) -> dict:
    source = _source_resolver(case)
    target_ids = set(case["reviewScope"]["targetClaimIds"])
    parties = {party["partyId"]: party for party in case["parties"]}
    processing = []
    timeline = [
        {
            "entryId": f"accident:{case['accident']['accidentId']}",
            "eventType": "accident",
            "occurredAt": case["accident"]["occurredAt"],
            "title": "事故发生",
            "detail": case["accident"]["description"],
            "sources": source(case["accident"].get("evidenceRefs")),
        }
    ]
    for item in case.get("calculations", []):
        processing.append(
            {
                "recordId": item["calculationId"],
                "recordType": "calculation",
                "claimId": item["claimId"],
                "title": "赔款计算",
                "status": item["status"],
                "occurredAt": None,
                "amount": _money(item.get("totalAmount")),
                "detail": item.get("adjustmentReason"),
                "sources": source(item.get("evidenceRefs")),
            }
        )
    for item in case.get("approvals", []):
        sources = source(item.get("evidenceRefs"))
        processing.append(
            {
                "recordId": item["approvalId"],
                "recordType": "approval",
                "claimId": item["claimId"],
                "title": "核赔审批",
                "status": item["status"],
                "occurredAt": item.get("decidedAt"),
                "amount": _money(item.get("approvedAmount")),
                "detail": item.get("reason"),
                "sources": sources,
            }
        )
        if item.get("decidedAt"):
            timeline.append(
                {
                    "entryId": f"approval:{item['approvalId']}",
                    "eventType": "approval",
                    "occurredAt": item["decidedAt"],
                    "title": "核赔决定",
                    "detail": item.get("reason"),
                    "sources": sources,
                }
            )
    for item in case.get("payments", []):
        sources = source(item.get("evidenceRefs"))
        processing.append(
            {
                "recordId": item["paymentId"],
                "recordType": "payment",
                "claimId": item["claimId"],
                "title": {"disbursement": "付款", "refund": "退款", "reversal": "冲销"}.get(item["kind"], item["kind"]),
                "status": item["status"],
                "occurredAt": item.get("occurredAt"),
                "amount": _money(item.get("amount")),
                "detail": f"交易号：{item.get('externalTransactionId', '未提供')}；收款对象：{item.get('payeePartyId') or '不适用'}",
                "sources": sources,
            }
        )
        timeline.append(
            {
                "entryId": f"payment:{item['paymentId']}",
                "eventType": "payment",
                "occurredAt": item["occurredAt"],
                "title": {"disbursement": "付款记录", "refund": "退款记录", "reversal": "冲销记录"}.get(item["kind"], "支付记录"),
                "detail": f"{item['status']} · {item['amount'].get('amountFen')} 分",
                "sources": sources,
            }
        )
    for claim in case["claims"]:
        timeline.append(
            {
                "entryId": f"closure:{claim['claimId']}",
                "eventType": "closure",
                "occurredAt": claim["closedAt"],
                "title": f"赔案结案 · {claim['claimNumber']}",
                "detail": f"{claim['closureType']}；支付状态 {claim['originalPaymentStatus']}",
                "sources": source(claim.get("evidenceRefs")),
            }
        )
    timeline.sort(key=lambda item: (item["occurredAt"], item["entryId"]))

    claims = []
    for claim in case["claims"]:
        role = "target" if claim["claimId"] in target_ids else "related"
        claims.append(
            _claim(claim, role)
            | {
                "handlingOrganization": claim["handlingOrganization"],
                "originalConclusion": claim["originalConclusion"],
                "sources": source(claim.get("evidenceRefs")),
            }
        )

    return {
        "id": case["datasetCaseId"],
        "revision": case["caseRevision"],
        "isSynthetic": case["isSynthetic"],
        "preparedAt": case["preparedAt"],
        "latestReviewStatus": "not_started",
        "scope": {
            "lossTypes": case["reviewScope"]["lossTypes"],
            "scopeLimitations": case["reviewScope"]["scopeLimitations"],
        },
        "accident": {
            **{key: case["accident"][key] for key in ("accidentId", "occurredAt", "location", "description", "liabilityDescription")},
            "sources": source(case["accident"].get("evidenceRefs")),
        },
        "injury": {
            "declaredStatus": case["injury"]["declaredStatus"],
            "injuredPersonIds": [item["partyId"] for item in case["injury"].get("injuredPersons", [])],
            "sources": source(case["injury"].get("evidenceRefs")),
        },
        "parties": [
            {key: party[key] for key in ("partyId", "displayName", "kind")} for party in case["parties"]
        ],
        "vehicles": [
            {
                "vehicleId": item["vehicleId"],
                "role": item["role"],
                "plateNumber": item["plateNumber"],
                "ownerName": parties.get(item.get("ownerPartyId"), {}).get("displayName"),
                "driverName": parties.get(item.get("driverPartyId"), {}).get("displayName"),
                "usage": item.get("usage"),
                "powerType": item.get("powerType"),
                "sources": source(item.get("evidenceRefs")),
            }
            for item in case["vehicles"]
        ],
        "claims": claims,
        "policies": [
            {
                "policyId": policy["policyId"],
                "policyNumber": policy.get("policyNumber"),
                "availability": policy["availability"],
                "policyType": policy["policyType"],
                "vehicleId": policy.get("vehicleId"),
                "effectiveFrom": policy.get("effectiveFrom"),
                "effectiveTo": policy.get("effectiveTo"),
                "coverages": [
                    {
                        "coverageId": coverage["coverageId"],
                        "coverageCode": coverage["coverageCode"],
                        "status": coverage["status"],
                        "insuranceAmount": _money(coverage.get("insuranceAmount")),
                        "perAccidentLimit": _money(coverage.get("perAccidentLimit")),
                        "deductibleAmount": _money(coverage.get("deductibleAmount")),
                        "deductibleBasisPoints": coverage.get("deductibleBasisPoints"),
                        "specialConditions": coverage.get("specialConditions"),
                        "terms": [
                            {key: term[key] for key in ("documentId", "version", "sectionIds")}
                            for term in coverage.get("terms", [])
                        ],
                        "sources": source(coverage.get("evidenceRefs")),
                    }
                    for coverage in policy.get("coverages", [])
                ],
                "sources": source(policy.get("evidenceRefs")),
            }
            for policy in case["policies"]
        ],
        "losses": [
            {
                "lossId": loss["lossId"],
                "claimId": loss["claimId"],
                "vehicleId": loss.get("vehicleId"),
                "personPartyId": loss.get("personPartyId"),
                "lossType": loss["lossType"],
                "description": loss["description"],
                "claimedAmount": _money(loss.get("claimedAmount")),
                "assessedAmount": _money(loss.get("assessedAmount")),
                "agreedAmount": _money(loss.get("agreedAmount")),
                "sources": source(loss.get("evidenceRefs")),
            }
            for loss in case["losses"]
        ],
        "processingRecords": processing,
        "timeline": timeline,
        "documents": [
            {
                "documentId": item["documentId"],
                "title": item["title"],
                "materialType": item["materialType"],
                "status": item["status"],
                "version": item["version"],
                "pageCount": item.get("pageCount"),
                "claimIds": item.get("claimIds", []),
                "entityIds": item.get("entityIds", []),
                "issuedAt": item.get("issuedAt"),
                "receivedAt": item.get("receivedAt"),
                "sourceDescription": item["sourceDescription"],
                "contentUrl": f"/api/review-cases/{quote(case['datasetCaseId'])}/documents/{quote(item['documentId'])}/content"
                if item["status"] == "available" and item.get("relativePath")
                else None,
            }
            for item in case["documents"]
        ],
        "dataGaps": [
            {
                "gapId": item["gapId"],
                "kind": item["kind"],
                "entityIds": item["entityIds"],
                "fieldPaths": item["fieldPaths"],
                "description": item["description"],
                "sources": source(item.get("evidenceRefs")),
            }
            for item in case.get("dataGaps", [])
        ],
        "originalApprovedAmount": _sum_approved(case, target_ids),
        "effectivePaidAmount": _sum_paid(case, target_ids),
    }


def get_review_case(case_id: str) -> dict | None:
    for _, case in _load_all():
        if case["datasetCaseId"] == case_id:
            return deepcopy(_detail(case))
    return None


def review_document(case_id: str, document_id: str) -> tuple[Path, str] | None:
    for case_dir, case in _load_all():
        if case["datasetCaseId"] != case_id:
            continue
        document = next((item for item in case["documents"] if item["documentId"] == document_id), None)
        if document is None or document["status"] != "available" or not document.get("relativePath"):
            return None
        path = (case_dir / document["relativePath"]).resolve()
        if not path.is_relative_to(case_dir) or not path.is_file():
            raise ReviewCaseDataError("案件材料路径无效。")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != document["sha256"]:
            raise ReviewCaseDataError("案件材料校验值不一致。")
        return path, document["title"]
    return None

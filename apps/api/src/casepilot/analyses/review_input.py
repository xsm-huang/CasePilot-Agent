"""Build immutable closed-claim review inputs and dependency preflight."""

from copy import deepcopy

from ..cases.review_repository import (
    ReviewCaseDataError,
    get_review_case_input,
    review_input_version,
    review_scope_items,
)
from ..knowledge.config import PROFILE
from .errors import AnalysisError


class ReviewInputBuilder:
    def __init__(self, knowledge):
        self.knowledge = knowledge

    async def _bindings(self, case):
        available = []
        if self.knowledge is not None:
            available = await self.knowledge.repository.list_documents()
        result = []
        for reference in case.get("knowledgeRefs", []):
            match = next(
                (
                    item
                    for item in available
                    if item.get("sha256") == reference.get("documentSha256")
                    and item.get("clauseVersion") == reference.get("version")
                    and item.get("status") == "ready"
                ),
                None,
            )
            result.append(
                {
                    **reference,
                    "status": "ready" if match else "unavailable",
                    "generationId": match.get("generationId") if match else None,
                    "productCode": match.get("productCode") if match else None,
                    "clauseVersion": match.get("clauseVersion") if match else None,
                    "embeddingProfile": PROFILE if match else None,
                }
            )
        return result

    async def build(self, case_id):
        try:
            case = get_review_case_input(case_id)
        except ReviewCaseDataError as error:
            raise AnalysisError("CASE_DATA_INVALID", str(error)) from error
        if case is None:
            raise AnalysisError("NOT_FOUND", "案件不存在。")
        scope_items = review_scope_items(case)
        bindings = await self._bindings(case)
        for binding in bindings:
            scope_items.append(
                {
                    "scopeItemId": f"terms:{binding['documentId']}",
                    "kind": "clause_verification",
                    "title": f"条款依据核对 · {binding['version']}",
                    "status": "executable" if binding["status"] == "ready" else "limited",
                    "entityIds": [binding["documentId"]],
                    "reason": None
                    if binding["status"] == "ready"
                    else "对应版本条款索引未取得，依赖该条款的判断无法完成。",
                    "requiredMaterialTypes": ["contract_terms"],
                }
            )
        blocking = [item["reason"] for item in scope_items if item["status"] == "blocked"]
        executable = any(item["status"] == "executable" for item in scope_items)
        if not executable:
            blocking.append("当前输入不能执行任何审查项目")
        status = (
            "blocked"
            if blocking
            else "partial"
            if any(item["status"] == "limited" for item in scope_items)
            or any(item["status"] == "unavailable" for item in bindings)
            else "ready"
        )
        material_summary = {"available": 0, "notObtained": 0, "unavailable": 0}
        for document in case.get("documents", []):
            if document.get("status") == "available":
                material_summary["available"] += 1
            elif document.get("status") == "not_obtained":
                material_summary["notObtained"] += 1
            else:
                material_summary["unavailable"] += 1
        version = review_input_version({"case": case, "knowledgeBindings": bindings})
        preflight = {
            "caseId": case_id,
            "expectedInputVersion": version,
            "status": status,
            "reviewObjects": {
                "targetClaimIds": case["reviewScope"]["targetClaimIds"],
                "relatedClaimIds": case["reviewScope"]["relatedClaimIds"],
                "vehicleIds": [item["vehicleId"] for item in case.get("vehicles", [])],
                "lossIds": [item["lossId"] for item in case.get("losses", [])],
                "scopeLimitations": case["reviewScope"].get("scopeLimitations", []),
            },
            "applicablePolicies": [
                {
                    "policyId": item["policyId"],
                    "policyType": item["policyType"],
                    "availability": item["availability"],
                    "coverageCodes": [
                        coverage["coverageCode"] for coverage in item.get("coverages", [])
                    ],
                }
                for item in case.get("policies", [])
            ],
            "scopeItems": scope_items,
            "knowledgeBindings": bindings,
            "materialSummary": material_summary,
            "injuryStatus": case["injury"]["declaredStatus"],
            "injuredPersonIds": [
                item["partyId"] for item in case["injury"].get("injuredPersons", [])
            ],
            "blockingReasons": blocking,
        }
        snapshot = {
            "snapshotKind": "closed_claim_review",
            "caseId": case_id,
            "caseRevision": case["caseRevision"],
            "preparedAt": case["preparedAt"],
            "payload": deepcopy(case),
            "scopeItems": deepcopy(scope_items),
            "knowledgeBindings": deepcopy(bindings),
        }
        return preflight, snapshot

    async def preflight(self, case_id):
        return (await self.build(case_id))[0]

    async def require_startable(self, case_id, expected_version):
        preflight, snapshot = await self.build(case_id)
        if preflight["status"] == "blocked":
            raise AnalysisError(
                "REVIEW_BLOCKED",
                "；".join(preflight["blockingReasons"]) or "当前案件无法启动审查。",
            )
        if expected_version != preflight["expectedInputVersion"]:
            raise AnalysisError("INPUT_VERSION_CONFLICT", "案件输入已变化，请刷新启动前检查。")
        return preflight, snapshot

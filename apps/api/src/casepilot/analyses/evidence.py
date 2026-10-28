"""Pinned facts and model output boundaries; provenance is owned by the server."""

from copy import deepcopy

from ..schemas.agent import Assessment, Fact
from .agent_errors import AgentError


def case_facts(claim: dict) -> list[dict]:
    """Create stable facts from the immutable closed-claim snapshot."""
    payload = claim.get("payload", claim)
    facts = []
    for field in ("reviewScope", "accident", "injury"):
        facts.append(Fact(factId=f"case:{field}", fieldPath=field, value=payload.get(field), sourceType="case").model_dump())
    collections = (
        ("claims", "claimId"), ("vehicles", "vehicleId"), ("policies", "policyId"),
        ("losses", "lossId"), ("calculations", "calculationId"),
        ("approvals", "approvalId"), ("payments", "paymentId"),
    )
    for collection, identifier in collections:
        for item in payload.get(collection, []):
            item_id = item.get(identifier)
            facts.append(Fact(factId=f"{collection}:{item_id}", fieldPath=f"{collection}[{item_id}]", value=item, sourceType="case").model_dump())
    for item in payload.get("documents", []):
        item_id = item["documentId"]
        facts.append(Fact(factId=f"documents:{item_id}", fieldPath=f"documents[{item_id}]", value=item, sourceType="material", materialId=item_id).model_dump())
    for item in payload.get("dataGaps", []):
        facts.append(Fact(factId=f"dataGaps:{item['gapId']}", fieldPath=f"dataGaps[{item['gapId']}]", value=item, sourceType="case").model_dump())
    for item in payload.get("reviewSupplements", []):
        for page in item.get("pages", []):
            facts.append(
                Fact(
                    factId=f"supplements:{item['supplementId']}:page:{page['page']}",
                    fieldPath=f"reviewSupplements[{item['supplementId']}].pages[{page['page']}]",
                    value=page["content"],
                    sourceType="material",
                    materialId=item["supplementId"],
                ).model_dump()
            )
    return facts


def checked_assessment(value, facts, citations):
    assessment = Assessment.model_validate(value)
    fact_ids = {fact["factId"] for fact in facts}
    citation_ids = {citation["citationId"] for citation in citations}
    for finding in assessment.findings:
        if not set(finding.factRefs) <= fact_ids or not set(finding.citationRefs) <= citation_ids:
            raise AgentError("ANALYSIS_REFERENCE_INVALID")
        if finding.evidenceStatus == "supported" and (
            not finding.factRefs or not finding.citationRefs
        ):
            raise AgentError("ANALYSIS_EVIDENCE_MISSING")
    result = assessment.model_dump()
    if not citations or any(f.evidenceStatus == "insufficient" for f in assessment.findings):
        result["insufficientEvidence"] = True
    return result


def merge_citations(previous, rows, context):
    """Never accept source metadata invented by the model or another knowledge generation."""
    merged = {row["chunkId"]: deepcopy(row) for row in previous}
    for row in rows:
        bindings = [item for item in context["knowledgeBindings"] if item["status"] == "ready"]
        if not any(
            row.get("productCode") == item["productCode"]
            and row.get("clauseVersion") == item["clauseVersion"]
            and row.get("generationId") == item["generationId"]
            for item in bindings
        ):
            raise AgentError("RETRIEVAL_SCOPE_INVALID")
        if (
            not isinstance(row.get("chunkId"), str)
            or not row["chunkId"]
            or type(row.get("page")) is not int
            or row["page"] < 1
            or not isinstance(row.get("content"), str)
            or not row["content"].strip()
        ):
            raise AgentError("RETRIEVAL_SOURCE_INVALID")
        if any(
            not isinstance(row.get(key), str) or not row[key] for key in ("documentId", "fileName")
        ):
            raise AgentError("RETRIEVAL_SOURCE_INVALID")
        citation = {key: deepcopy(value) for key, value in row.items() if key != "distance"}
        citation["citationId"] = row["chunkId"]
        if row["chunkId"] in merged and merged[row["chunkId"]] != citation:
            raise AgentError("RETRIEVAL_SOURCE_CHANGED")
        merged[row["chunkId"]] = citation
    if len(merged) > 12:
        raise AgentError("RETRIEVAL_LIMIT_EXCEEDED")
    return list(merged.values())

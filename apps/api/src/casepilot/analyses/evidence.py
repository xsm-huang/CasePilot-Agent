"""Pinned facts and model output boundaries; provenance is owned by the server."""

from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from .agent_errors import AgentError


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Fact(StrictModel):
    factId: str
    fieldPath: str
    value: JsonValue
    sourceType: Literal["case", "material"]
    materialId: str | None = None


class ModelFinding(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    inference: str = Field(min_length=1, max_length=2000)
    evidenceStatus: Literal["supported", "insufficient"]
    factRefs: list[str] = Field(max_length=30)
    citationRefs: list[str] = Field(max_length=12)
    pendingItems: list[str] = Field(max_length=12)


class Assessment(StrictModel):
    summary: str = Field(min_length=1, max_length=3000)
    findings: list[ModelFinding] = Field(max_length=20)
    insufficientEvidence: bool
    pendingItems: list[str] = Field(max_length=12)


def case_facts(claim: dict) -> list[dict]:
    """Stable references address the immutable snapshot, including missing required dates."""
    facts = [
        Fact(
            factId="materials:types",
            fieldPath="materials[*].type",
            value=[material.get("type") for material in claim.get("materials", [])],
            sourceType="case",
        ).model_dump()
    ]
    for field in sorted(set(claim) - {"materials"} | {"accidentDate", "policyEffectiveDate"}):
        facts.append(
            Fact(
                factId=f"case:{field}", fieldPath=field, value=claim.get(field), sourceType="case"
            ).model_dump()
        )
    for index, material in enumerate(claim.get("materials", [])):
        material_id = f"{claim['id']}:material:{index}"
        fields = material.get("fields", {})
        names = set(fields)
        if material.get("type") in {"claim_form", "accident_certificate"}:
            names.add("accidentDate")
        for field in sorted(names):
            facts.append(
                Fact(
                    factId=f"material:{index}:{field}",
                    fieldPath=f"materials[{index}].fields.{field}",
                    value=fields.get(field),
                    sourceType="material",
                    materialId=material_id,
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
        if any(
            row.get(key) != context[key] for key in ("productCode", "clauseVersion", "generationId")
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

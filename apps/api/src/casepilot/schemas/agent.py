"""Shared strict evidence models, without application initialization."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Fact(StrictModel):
    factId: str
    fieldPath: str
    value: JsonValue
    sourceType: Literal["case", "material", "business"]
    materialId: str | None = None


class ModelFinding(StrictModel):
    relatedCheckId: str | None = None
    issueCode: str = Field(min_length=1, max_length=100)
    supportQuote: str = Field(max_length=500)
    category: Literal["issue", "limitation", "out_of_scope", "passed"] = "issue"
    nodeKey: Literal["archive", "coverage", "consistency", "clauses", "amount", "report"] = (
        "clauses"
    )
    title: str = Field(min_length=1, max_length=200)
    inference: str = Field(min_length=1, max_length=2000)
    evidenceStatus: Literal["supported", "insufficient"]
    factRefs: list[str] = Field(max_length=30)
    citationRefs: list[str] = Field(max_length=12)
    pendingItems: list[str] = Field(max_length=12)


class AssessmentFinding(ModelFinding):
    category: Literal["issue", "limitation", "out_of_scope", "passed"]
    nodeKey: Literal["archive", "coverage", "consistency", "clauses", "amount", "report"]


class Assessment(StrictModel):
    summary: str = Field(min_length=1, max_length=3000)
    findings: list[AssessmentFinding] = Field(max_length=20)
    checkedItems: list[AssessmentFinding] = Field(min_length=1, max_length=20)
    insufficientEvidence: bool
    pendingItems: list[str] = Field(max_length=12)


class ReviewCheck(StrictModel):
    checkId: str
    nodeKey: Literal["archive", "coverage", "consistency", "clauses", "amount", "report"]
    status: Literal["passed", "issue", "limited", "not_applicable", "out_of_scope"]
    source: Literal["rule", "ai", "human"]
    sources: list[Literal["rule", "ai", "human"]] = Field(default_factory=list)
    title: str
    detail: str
    factRefs: list[str] = Field(default_factory=list)
    citationRefs: list[str] = Field(default_factory=list)
    entityIds: list[str] = Field(default_factory=list)
    policyIds: list[str] = Field(default_factory=list)
    coverageIds: list[str] = Field(default_factory=list)
    originalValues: dict[str, JsonValue] = Field(default_factory=dict)
    uncertainty: str = ""
    recommendation: str = ""
    statements: list[dict[str, JsonValue]] = Field(default_factory=list)


class FindingReview(StrictModel):
    reviewId: str
    findingId: str
    nodeKey: str
    decision: Literal["confirmed", "excluded", "pending", "referred"]
    comment: str
    operatorId: str
    at: str
    factRefs: list[str]
    citationRefs: list[str]
    supplementIds: list[str]
    followup: str
    changeReason: str
    findingVersion: int
    previousReviewId: str
    recipient: str
    missingItems: str
    evidenceViewed: bool

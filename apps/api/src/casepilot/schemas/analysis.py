from datetime import timezone
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_serializer


class DTO(BaseModel):
    model_config = ConfigDict(strict=True)


class V0Material(DTO):
    type: str
    name: str
    fields: dict[str, str | float]


class V0ClaimCase(DTO):
    id: str
    claimant: str
    productCode: str
    clauseVersion: str
    policyEffectiveDate: str
    accidentDate: str
    claimAmount: float
    materials: list[V0Material]


class V0Finding(DTO):
    code: str
    source: Literal["rule", "ai"]
    severity: Literal["low", "medium", "high"]
    title: str
    detail: str


class V0ClauseCitation(DTO):
    id: str
    title: str
    content: str
    score: float


class V0Clause(DTO):
    id: str
    productCode: str
    version: str
    title: str
    content: str
    keywords: list[str]


class V0ReviewAccepted(DTO):
    accepted: Literal[True]
    taskId: str


class V0Review(DTO):
    decision: Literal["approve", "reject"]
    comment: str = Field(default="", max_length=2000)


class V0AnalysisReport(DTO):
    caseId: str
    summary: str
    findings: list[V0Finding]
    recommendation: str
    citations: list[V0ClauseCitation]
    reviewerComment: str | None = None


Status = Literal["running", "waiting_review", "completed", "rejected", "failed"]


class V0TimelineEvent(DTO):
    id: int = Field(gt=0, le=2**53 - 1)
    type: Literal["status", "node", "tool", "review_required", "report", "error"]
    at: AwareDatetime = Field(strict=False)
    title: str
    detail: str | None = None
    data: list[V0Finding] | list[V0ClauseCitation] | V0AnalysisReport | dict[str, Any] | None = None
    status: Status

    @field_serializer("at")
    def serialize_at(self, value: AwareDatetime) -> str:
        """Match the persisted SSE wire format exactly in every JSON snapshot."""
        return (
            value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        )


class V0AnalysisTask(DTO):
    id: str
    caseId: str
    status: Status
    events: list[V0TimelineEvent]
    findings: list[V0Finding]
    citations: list[V0ClauseCitation]
    report: V0AnalysisReport | None = None
    review: V0Review | None = None

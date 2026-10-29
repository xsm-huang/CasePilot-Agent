"""Business execution and append-only manual review contracts."""

from typing import Literal

from pydantic import Field, JsonValue

from .agent import ReviewCheck, StrictModel

NodeKey = Literal["archive", "coverage", "consistency", "clauses", "amount", "report"]
NodeStatus = Literal["not_started", "running", "completed", "failed", "unable", "not_applicable"]


class CheckPlanItem(StrictModel):
    checkId: str
    nodeKey: NodeKey
    title: str
    required: bool
    entityIds: list[str]


class BusinessNode(StrictModel):
    nodeRunId: str
    nodeKey: NodeKey
    attempt: int
    status: NodeStatus
    startedAt: str | None
    endedAt: str | None
    durationMs: int
    summary: str
    reason: str


class Finding(ReviewCheck):
    findingId: str
    version: int
    kind: Literal["issue", "limitation", "out_of_scope"]
    active: bool = True


class Eligibility(StrictModel):
    allowed: bool
    blockers: list[str]
    basisHash: str


class ReviewRecord(StrictModel):
    recordId: str
    kind: Literal[
        "evidence_view",
        "human_completion",
        "scope_adjustment",
        "professional",
        "followup",
        "business_record",
        "reopen",
    ]
    nodeKey: NodeKey
    targetId: str
    comment: str
    operatorId: str
    at: str
    factRefs: list[str]
    citationRefs: list[str]
    supplementIds: list[str]
    checkIds: list[str]
    steps: str
    result: str
    recipient: str
    state: str
    source: str
    previousRecordId: str
    inputsFen: list[int]
    operation: Literal["sum", "difference"] | None
    resultFen: int | None


class ReviewState(StrictModel):
    reviewModelVersion: Literal[1]
    checkPlan: list[CheckPlanItem]
    checks: list[ReviewCheck]
    findings: list[Finding]
    findingHistory: list[Finding]
    records: list[ReviewRecord]
    businessNodes: list[BusinessNode]
    nodeHistory: list[BusinessNode]
    reviewCycleId: int


class ReviewRecordRequest(StrictModel):
    expectedRevision: int = Field(ge=0)
    nodeKey: NodeKey
    targetId: str = ""
    comment: str = Field(min_length=5, max_length=2000)
    factRefs: list[str] = Field(default_factory=list, max_length=30)
    citationRefs: list[str] = Field(default_factory=list, max_length=12)
    supplementIds: list[str] = Field(default_factory=list, max_length=20)
    checkIds: list[str] = Field(default_factory=list, max_length=50)
    steps: str = Field(default="", max_length=3000)
    result: str = Field(default="", max_length=3000)
    recipient: str = Field(default="", max_length=200)
    state: str = Field(default="", max_length=50)
    source: str = Field(default="", max_length=500)
    previousRecordId: str = ""
    inputsFen: list[int] = Field(default_factory=list, max_length=30)
    operation: Literal["sum", "difference"] | None = None
    resultFen: int | None = None


class ManualFindingRequest(StrictModel):
    expectedRevision: int = Field(ge=0)
    nodeKey: NodeKey
    title: str = Field(min_length=2, max_length=200)
    detail: str = Field(min_length=5, max_length=2000)
    entityIds: list[str] = Field(min_length=1, max_length=30)
    factRefs: list[str] = Field(default_factory=list, max_length=30)
    citationRefs: list[str] = Field(default_factory=list, max_length=12)
    supplementIds: list[str] = Field(default_factory=list, max_length=20)
    originalValues: dict[str, JsonValue] = Field(default_factory=dict)
    recommendation: str = Field(min_length=2, max_length=1000)

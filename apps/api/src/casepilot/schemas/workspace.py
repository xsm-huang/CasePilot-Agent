"""Closed-claim review workspace transport models."""

from typing import Annotated, Literal

from pydantic import Field, JsonValue, RootModel

from .agent import Fact, FindingReview, ModelFinding, ReviewCheck, StrictModel
from .knowledge import Timestamp
from .review import BusinessNode, Eligibility, ReviewState
from .review_cases import ClosedClaimReviewSnapshot, ReviewCaseListItem, ReviewKnowledgeBinding

AnalysisStatus = Literal[
    "queued",
    "running",
    "waiting_review",
    "resuming",
    "recoverable",
    "completed",
    "rejected",
    "failed",
]
SectionKey = Literal["summary", "coverage", "findings", "limitations", "reviews", "recommendations"]


class PublicError(StrictModel):
    code: str
    message: str
    requestId: str


class SourceValue(StrictModel):
    factId: str
    value: JsonValue


class RuleFinding(StrictModel):
    code: str
    source: Literal["rule"]
    severity: Literal["low", "medium", "high"]
    title: str
    detail: str
    factRefs: list[str]
    sourceValues: list[SourceValue]


class Citation(StrictModel):
    citationId: str
    chunkId: str
    generationId: str
    documentId: str
    fileName: str
    productCode: str
    clauseVersion: str
    page: int = Field(gt=0)
    ordinal: int = Field(ge=0)
    content: str


class CitationBlock(StrictModel):
    chunkId: str
    page: int = Field(gt=0)
    ordinal: int = Field(ge=0)
    content: str


class CitationContext(StrictModel):
    citation: Citation
    previous: CitationBlock | None
    next: CitationBlock | None


class ReportSection(StrictModel):
    sectionKey: SectionKey
    content: str = Field(min_length=1, max_length=6000)
    factRefs: list[str]
    citationRefs: list[str]
    committedAt: Timestamp


class AnalysisReport(StrictModel):
    kind: Literal["pending_review", "stage", "final"] = "stage"
    version: int
    analysisId: str = ""
    inputVersion: str = ""
    generatedAt: str = ""
    operatorId: str | None = None
    conclusion: str = "历史报告，业务完成条件需核对"
    caseId: str
    sections: list[ReportSection]
    insufficientEvidence: bool
    reviewerComment: str | None
    basisHash: str
    snapshot: dict[str, JsonValue]
    statistics: dict[str, int]
    revisionReason: str
    replacesVersion: int | None


class PendingReview(StrictModel):
    interruptKey: str
    checkpointId: str
    revision: int = Field(ge=0)
    reason: str


class AnalysisContext(StrictModel):
    inputVersion: str
    knowledgeBindings: list[ReviewKnowledgeBinding]
    messageIds: list[str]
    modelProfile: str
    promptVersion: str


class StatusData(StrictModel):
    status: AnalysisStatus
    revision: int


class ExecutionData(StrictModel):
    nodeKey: Literal["archive", "coverage", "consistency", "clauses", "amount", "report"] = "report"
    executionId: str
    key: str
    name: str
    attempt: int = Field(gt=0)
    status: Literal["running", "completed", "failed"]
    summary: str
    durationMs: int = Field(ge=0)
    kind: Literal["local", "retrieval", "model"]
    parentNodeRunId: str


class AnalysisReadyData(StrictModel):
    checks: list[ReviewCheck] = Field(default_factory=list)
    facts: list[Fact]
    ruleFindings: list[RuleFinding]
    modelFindings: list[ModelFinding]
    citations: list[Citation]
    insufficientEvidence: bool


class ReviewAcceptedData(StrictModel):
    interruptKey: str
    decision: Literal["approve", "reject"]
    revision: int
    comment: str = ""
    operatorId: str = "unidentified_operator"
    nodeKey: str = "report"


class ReportCompletedData(StrictModel):
    report: AnalysisReport
    assistantMessageId: str
    revision: int


class FailureData(StrictModel):
    error: PublicError
    revision: int


class RejectedData(StrictModel):
    comment: str
    revision: int


class SupplementPage(StrictModel):
    page: int = Field(gt=0)
    content: str


class EvidenceSupplement(StrictModel):
    nodeKey: Literal["archive", "coverage", "consistency", "clauses", "amount", "report"] = "amount"
    supplementId: str
    version: int = Field(gt=0)
    analysisId: str
    title: str
    materialType: str
    entityIds: list[str]
    sha256: str = Field(pattern="^[a-f0-9]{64}$")
    addedAt: Timestamp
    addedBy: str
    pages: list[SupplementPage]


class SupplementedData(StrictModel):
    supplement: EvidenceSupplement
    revision: int


class FindingReviewedData(StrictModel):
    review: FindingReview
    report: AnalysisReport
    revision: int


class EventBase(StrictModel):
    schemaVersion: Literal[2]
    analysisId: str
    conversationId: str
    seq: int = Field(gt=0, le=2**53 - 1)
    revision: int = Field(ge=0)
    at: Timestamp


class StatusEvent(EventBase):
    type: Literal["analysis.status"]
    data: StatusData


class ExecutionEvent(EventBase):
    type: Literal[
        "tool.started",
        "tool.completed",
        "tool.failed",
    ]
    data: ExecutionData


class ReadyEvent(EventBase):
    type: Literal["analysis.ready"]
    data: AnalysisReadyData


class ReviewEvent(EventBase):
    type: Literal["review.required"]
    data: PendingReview


class AcceptedEvent(EventBase):
    type: Literal["review.accepted"]
    data: ReviewAcceptedData


class SectionEvent(EventBase):
    type: Literal["report.section"]
    data: ReportSection


class CompletedEvent(EventBase):
    type: Literal["report.completed"]
    data: ReportCompletedData


class FailureEvent(EventBase):
    type: Literal["analysis.failed", "analysis.recoverable"]
    data: FailureData


class RejectedEvent(EventBase):
    type: Literal["analysis.rejected"]
    data: RejectedData


class SupplementedEvent(EventBase):
    type: Literal["evidence.supplemented"]
    data: SupplementedData


class FindingReviewedEvent(EventBase):
    type: Literal["finding.reviewed"]
    data: FindingReviewedData


class ReportSavedEvent(EventBase):
    type: Literal["report.saved"]
    data: AnalysisReport


class BusinessNodeEvent(EventBase):
    type: Literal[
        "business_node.started",
        "business_node.completed",
        "business_node.failed",
        "business_node.unable",
        "business_node.not_applicable",
    ]
    data: BusinessNode


class ReviewUpdatedEvent(EventBase):
    type: Literal["review.updated"]
    data: ReviewState


EventEnvelope = Annotated[
    StatusEvent
    | ExecutionEvent
    | ReadyEvent
    | ReviewEvent
    | AcceptedEvent
    | SectionEvent
    | CompletedEvent
    | FailureEvent
    | RejectedEvent
    | SupplementedEvent
    | FindingReviewedEvent
    | ReportSavedEvent
    | BusinessNodeEvent
    | ReviewUpdatedEvent,
    Field(discriminator="type"),
]


class WorkspaceEvent(RootModel[EventEnvelope]):
    pass


class Execution(StrictModel):
    tools: list[ExecutionData]
    timeline: list[EventEnvelope]


class AnalysisTask(StrictModel):
    reviewState: ReviewState
    finalizationEligibility: Eligibility
    reviewStatus: Literal["pending_review", "reviewing", "pending_verification", "completed"]
    caseSummary: ReviewCaseListItem | None = None
    checks: list[ReviewCheck] = Field(default_factory=list)
    reviewHistory: list[FindingReview] = Field(default_factory=list)
    reports: list[AnalysisReport] = Field(default_factory=list)
    operatorId: str = "unidentified_operator"
    schemaVersion: Literal[2]
    id: str
    caseId: str
    conversationId: str
    kind: Literal["initial", "followup"]
    question: str
    status: AnalysisStatus
    caseSnapshot: ClosedClaimReviewSnapshot
    predecessorAnalysisId: str | None
    evidenceSupplements: list[EvidenceSupplement]
    reviewSupplementIds: list[str]
    revision: int = Field(ge=0)
    lastEventSeq: int = Field(ge=0)
    userMessageId: str
    assistantMessageId: str | None
    context: AnalysisContext
    facts: list[Fact]
    ruleFindings: list[RuleFinding]
    modelFindings: list[ModelFinding]
    citations: list[Citation]
    sections: list[ReportSection]
    report: AnalysisReport | None
    pendingReview: PendingReview | None
    execution: Execution
    error: PublicError | None


class ConversationSummary(StrictModel):
    id: str
    caseId: str
    title: str
    createdAt: Timestamp
    updatedAt: Timestamp
    activeAnalysisId: str | None


class Message(StrictModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    analysisId: str
    createdAt: Timestamp


class Conversation(ConversationSummary):
    messages: list[Message]
    analysisIds: list[str]
    context: AnalysisContext | None
    nextBefore: str | None


class CreateConversation(StrictModel):
    title: str = Field(default="新会话", min_length=1, max_length=200)


class CreateAnalysis(StrictModel):
    conversationId: str = Field(min_length=1, max_length=200)
    kind: Literal["initial", "followup"]
    question: str | None = Field(default=None, max_length=2000)
    expectedInputVersion: str | None = Field(default=None, min_length=64, max_length=64)
    predecessorAnalysisId: str | None = Field(default=None, min_length=1, max_length=200)
    supplementIds: list[str] = Field(default_factory=list)


class ReviewRequest(StrictModel):
    decision: Literal["approve", "reject"]
    comment: str = Field(default="", max_length=2000)
    interruptKey: str = Field(min_length=1, max_length=200)
    expectedRevision: int = Field(ge=0)
    supplementIds: list[str] = Field(default_factory=list)
    coverageConfirmed: bool = False
    reviewCycleId: int = Field(gt=0)
    reportVersion: int = Field(gt=0)
    basisHash: str = Field(min_length=64, max_length=64)


class FindingReviewRequest(StrictModel):
    decision: Literal["confirmed", "excluded", "pending", "referred"]
    comment: str = Field(min_length=2, max_length=2000)
    expectedRevision: int = Field(ge=0)
    factRefs: list[str] = Field(default_factory=list, max_length=30)
    citationRefs: list[str] = Field(default_factory=list, max_length=12)
    supplementIds: list[str] = Field(default_factory=list, max_length=20)
    followup: str = Field(default="", max_length=1000)
    changeReason: str = Field(default="", max_length=1000)
    findingVersion: int = Field(gt=0)
    previousReviewId: str = ""
    recipient: str = Field(default="", max_length=200)
    missingItems: str = Field(default="", max_length=1000)
    evidenceViewed: bool = False


class RecoverRequest(StrictModel):
    expectedRevision: int = Field(ge=0)


class CommandAccepted(StrictModel):
    accepted: Literal[True]
    taskId: str
    revision: int

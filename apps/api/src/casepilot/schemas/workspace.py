"""Versioned workspace transport models, including immutable legacy reads."""

from typing import Annotated, Literal

from pydantic import Field, JsonValue, RootModel

from .agent import Fact, ModelFinding, StrictModel
from .analysis import V0AnalysisTask, V0ClaimCase
from .knowledge import Timestamp

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
SectionKey = Literal["summary", "findings", "recommendations"]


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
    caseId: str
    sections: list[ReportSection]
    insufficientEvidence: bool
    reviewerComment: str | None


class PendingReview(StrictModel):
    interruptKey: str
    checkpointId: str
    revision: int = Field(ge=0)
    reason: str


class AnalysisContext(StrictModel):
    caseVersion: str
    generationId: str
    embeddingProfile: str
    messageIds: list[str]
    modelProfile: str
    promptVersion: str


class StatusData(StrictModel):
    status: AnalysisStatus
    revision: int


class ExecutionData(StrictModel):
    executionId: str
    key: str
    name: str
    attempt: int = Field(gt=0)
    status: Literal["running", "completed", "failed"]
    summary: str
    durationMs: int = Field(ge=0)


class AnalysisReadyData(StrictModel):
    facts: list[Fact]
    ruleFindings: list[RuleFinding]
    modelFindings: list[ModelFinding]
    citations: list[Citation]
    insufficientEvidence: bool


class ReviewAcceptedData(StrictModel):
    interruptKey: str
    decision: Literal["approve", "reject"]
    revision: int


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


class EventBase(StrictModel):
    schemaVersion: Literal[1]
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
        "node.started",
        "node.completed",
        "node.failed",
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


EventEnvelope = Annotated[
    StatusEvent
    | ExecutionEvent
    | ReadyEvent
    | ReviewEvent
    | AcceptedEvent
    | SectionEvent
    | CompletedEvent
    | FailureEvent
    | RejectedEvent,
    Field(discriminator="type"),
]


class WorkspaceEvent(RootModel[EventEnvelope]):
    pass


class Execution(StrictModel):
    nodes: list[ExecutionData]
    tools: list[ExecutionData]
    timeline: list[EventEnvelope]


class V1AnalysisTask(StrictModel):
    schemaVersion: Literal[1]
    id: str
    caseId: str
    conversationId: str
    kind: Literal["initial", "followup"]
    question: str
    status: AnalysisStatus
    caseSnapshot: V0ClaimCase
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


class LegacyAnalysisTask(V0AnalysisTask):
    schemaVersion: Literal[0]
    readOnly: Literal[True]


class WorkbenchTask(
    RootModel[Annotated[V1AnalysisTask | LegacyAnalysisTask, Field(discriminator="schemaVersion")]]
):
    pass


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


class ReviewRequest(StrictModel):
    decision: Literal["approve", "reject"]
    comment: str = Field(default="", max_length=2000)
    interruptKey: str = Field(min_length=1, max_length=200)
    expectedRevision: int = Field(ge=0)


class RecoverRequest(StrictModel):
    expectedRevision: int = Field(ge=0)


class CommandAccepted(StrictModel):
    accepted: Literal[True]
    taskId: str
    revision: int

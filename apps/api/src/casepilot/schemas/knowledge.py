"""Knowledge ingestion wire models. Generation and business version are distinct."""

from datetime import timezone
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, PlainSerializer

SafeInt = Annotated[int, Field(ge=0, le=2**53 - 1)]
PositiveInt = Annotated[int, Field(ge=1, le=2**53 - 1)]
Timestamp = Annotated[
    AwareDatetime,
    Field(strict=False),
    PlainSerializer(
        lambda value: (
            value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        ),
        return_type=str,
    ),
]


class V1DTO(BaseModel):
    model_config = ConfigDict(strict=True)


class V1KnowledgeError(V1DTO):
    code: str
    message: str
    reasonCode: str | None = None
    providerCode: str | None = None
    httpStatus: int | None = None
    requestId: str | None = None
    retryAfter: int | None = None


class V1KnowledgeAttempt(V1DTO):
    attempt: PositiveInt
    status: Literal["queued", "parsing", "chunking", "embedding", "ready", "failed"]
    startedAt: Timestamp
    finishedAt: Timestamp | None = None
    error: V1KnowledgeError | None = None


class V1KnowledgeGeneration(V1DTO):
    generationId: str
    documentId: str
    productCode: str
    clauseVersion: str
    fileName: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["queued", "parsing", "chunking", "embedding", "ready", "failed"]
    revision: PositiveInt
    attempt: PositiveInt
    pageCount: SafeInt
    chunkCount: SafeInt
    embeddedCount: SafeInt
    isActive: bool
    error: V1KnowledgeError | None = None
    createdAt: Timestamp
    updatedAt: Timestamp
    attempts: list[V1KnowledgeAttempt]


class V1KnowledgeRetry(V1DTO):
    expectedRevision: PositiveInt

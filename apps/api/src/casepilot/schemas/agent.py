"""Shared strict evidence models, without application initialization."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


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

"""Checkpoint state; field names remain compatible with existing tasks."""

from typing import TypedDict


class State(TypedDict, total=False):
    taskId: str
    caseId: str
    claim: dict
    findings: list[dict]
    citations: list[dict]
    review: dict
    report: dict

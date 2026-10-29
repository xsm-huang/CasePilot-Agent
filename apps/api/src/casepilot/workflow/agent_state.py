"""Bounded graph state, independent of the workspace checkpoint protocol."""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    facts: list[dict]
    ruleFindings: list[dict]
    checks: list[dict]
    citations: list[dict]
    queries: list[str]
    messages: list[dict]
    decisions: int
    supplements: int
    pendingTool: dict | None
    stopReason: str | None
    assessment: dict
    result: dict

"""Deterministic G3 collaborators. No live model or embedding requests."""

from copy import deepcopy

from casepilot.model.config import read_model_config


class RecordingRepository:
    """Explicit persistence test double; production memory mode remains rejected."""

    def __init__(self):
        self.snapshots = []

    async def save(self, task):
        self.snapshots.append(deepcopy(task))


def clause(number=1, generation="generation-1"):
    return {
        "chunkId": f"chunk-{number}",
        "page": number,
        "content": f"Article {number}: provide evidence of repair cost.",
        "ordinal": number - 1,
        "distance": 0.1,
        "documentId": "document-1",
        "fileName": "条款.pdf",
        "generationId": generation,
        "productCode": "AUTO-COMPREHENSIVE",
        "clauseVersion": "2025-01",
    }


def assessment(*, fact="case:accidentDate", citation="chunk-1", insufficient=False):
    return {
        "summary": "依据当前事实与条款，仍需核查事故和费用。",
        "findings": [
            {
                "title": "核查费用依据",
                "inference": "需结合原文核查材料。",
                "evidenceStatus": "insufficient" if insufficient else "supported",
                "factRefs": [fact],
                "citationRefs": [citation] if citation else [],
                "pendingItems": ["核查费用原件"],
            }
        ],
        "insufficientEvidence": insufficient,
        "pendingItems": [],
    }


def tool_turn(query, name="search_clauses", **extra):
    return {
        "content": "",
        "toolCalls": [{"id": "call-1", "name": name, "arguments": {"query": query, **extra}}],
        "usage": {},
    }


class FakeKnowledge:
    def __init__(self, responses=None):
        self.repository = self
        self.active = "generation-1"
        self.status = "ready"
        self.responses = responses or [[clause()]]
        self.calls = []

    async def active_generation(self, product, version):
        return self.active

    async def get_generation(self, generation):
        return {
            "generationId": generation,
            "status": self.status,
            "productCode": "AUTO-COMPREHENSIVE",
            "clauseVersion": "2025-01",
        }

    async def search(self, product, version, generation, query, limit, profile):
        self.calls.append((product, version, generation, query, limit, profile))
        return deepcopy(self.responses[min(len(self.calls) - 1, len(self.responses) - 1)])


class ScriptedChat:
    def __init__(self, decisions=None, assessments=None):
        self.config = read_model_config({"ZHIPU_API_KEY": "test-no-network"})
        self.decisions = list(decisions or [])
        self.assessments = list(assessments or [])
        self.calls = []

    async def complete(self, messages, *, tools=None, json_mode=False):
        import json

        self.calls.append(
            {"messages": deepcopy(messages), "tools": deepcopy(tools), "json": json_mode}
        )
        if tools:
            return (
                self.decisions.pop(0)
                if self.decisions
                else {"content": "进入结构化分析。", "toolCalls": [], "usage": {}}
            )
        output = self.assessments.pop(0) if self.assessments else assessment()
        return {
            "content": output
            if isinstance(output, str)
            else json.dumps(output, ensure_ascii=False),
            "toolCalls": [],
            "usage": {},
        }

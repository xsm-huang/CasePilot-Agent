"""Closed-claim analysis, approval interrupt and three section nodes."""

from langgraph.types import interrupt

from ..analyses.agent import run_agent_analysis
from ..analyses.sections import generate_section


class WorkspaceNodes:
    def __init__(self, store, knowledge, chat_factory):
        self.store, self.knowledge, self.chat_factory = store, knowledge, chat_factory

    async def analyze(self, state):
        task = self.store.get(state["taskId"])
        result = task["_artifacts"].get("analysis")
        if result is None:
            result = await run_agent_analysis(
                self.store,
                task["id"],
                self.knowledge,
                self.chat_factory(),
                question=task["question"],
            )
        await self.store.analysis_ready(task["id"], result)
        return {"analysis": result}

    def human(self, state):
        return {"review": interrupt({"taskId": state["taskId"], "needsReview": True})}

    async def summary(self, state):
        await generate_section(self.store, state["taskId"], "summary", self.chat_factory())
        return {}

    async def findings(self, state):
        await generate_section(self.store, state["taskId"], "findings", self.chat_factory())
        return {}

    async def recommendations(self, state):
        await generate_section(self.store, state["taskId"], "recommendations", self.chat_factory())
        return {}

    async def complete(self, state):
        await self.store.finalize(state["taskId"])
        return {}

    async def reject(self, state):
        await self.store.reject(state["taskId"])
        return {}

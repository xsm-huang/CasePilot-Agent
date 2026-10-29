"""Run automatic checks and persist the report aggregation stage."""

from ..analyses.agent import run_agent_analysis


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
        await self.store.start_business_node(task["id"], "report")
        await self.store.analysis_ready(task["id"], result)
        return {"analysis": result}

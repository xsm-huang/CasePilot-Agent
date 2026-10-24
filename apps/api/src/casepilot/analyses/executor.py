"""Durable command execution and checkpoint/projection reconciliation."""

from langgraph.types import Command

from ..cases.repository import get_case
from .status import TERMINAL


class Executor:
    def __init__(self, store, graph):
        self.store, self.graph = store, graph

    @staticmethod
    def config(task_id):
        return {"configurable": {"thread_id": task_id}}

    async def execute(self, command):
        task_id = command["taskId"]
        try:
            if self.store.get(task_id)["status"] in TERMINAL:
                await self.store.finish_command(command)
                return
            config = self.config(task_id)
            snapshot = await self.graph.aget_state(config)
            if command["kind"] == "review":
                review = command["review"]
                await self.store.mutate(
                    task_id,
                    event=(
                        "status",
                        "审核通过，恢复执行"
                        if review["decision"] == "approve"
                        else "审核驳回，恢复执行",
                        review["comment"],
                        None,
                    ),
                    key="review-accepted",
                )
                value = Command(resume=review) if "human_review" in snapshot.next else None
            elif snapshot.values:
                value = None
            else:
                task = self.store.get(task_id)
                value = {
                    "taskId": task_id,
                    "caseId": task["caseId"],
                    "claim": get_case(task["caseId"]),
                    "findings": [],
                    "citations": [],
                }
            await self.graph.ainvoke(value, config)
            snapshot = await self.graph.aget_state(config)
            if "human_review" in snapshot.next:
                await self.store.mutate(
                    task_id,
                    {"status": "waiting_review"},
                    (
                        "review_required",
                        "需要人工审核",
                        "规则发现疑点。审核仅决定是否继续分析，不代表赔付审批。",
                        self.store.get(task_id)["findings"],
                    ),
                    key="review-required",
                )
            await self.store.finish_command(command)
        except Exception as exc:
            # Persist the command outcome and task failure; do not silently lose a worker error.
            await self.store.mutate(
                task_id,
                {"status": "failed"},
                ("error", "工作流执行失败", type(exc).__name__, None),
                key="failure",
            )
            await self.store.finish_command(command, type(exc).__name__)

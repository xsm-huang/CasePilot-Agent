"""Consume V1 commands without replaying ambiguous external effects automatically."""

from langgraph.types import Command
from psycopg import Error as DatabaseError
from psycopg_pool import PoolTimeout

from ..knowledge.errors import KnowledgeOperationError
from ..model.errors import ModelError
from .agent_errors import AgentError
from .errors import AnalysisError
from .workspace_store import TERMINAL


class WorkspaceExecutor:
    def __init__(self, store, graph):
        self.store, self.graph = store, graph

    @staticmethod
    def config(task_id):
        return {"configurable": {"thread_id": f"v1:{task_id}"}}

    async def execute(self, command):
        task_id = command["taskId"]
        if self.store.get(task_id)["status"] in TERMINAL | {"recoverable"}:
            await self.store.finish_command(command)
            return
        try:
            config = self.config(task_id)
            snapshot = await self.graph.aget_state(config)
            review = command.get("review") or self.store.get(task_id).get("_review")
            if "human_review" in snapshot.next and not review:
                await self.store.waiting_review(
                    task_id, snapshot.config["configurable"]["checkpoint_id"]
                )
            else:
                await self.store.start(task_id, command["kind"])
                value = (
                    Command(resume=review)
                    if review and "human_review" in snapshot.next
                    else None
                    if snapshot.values
                    else {"taskId": task_id}
                )
                await self.graph.ainvoke(value, config)
                snapshot = await self.graph.aget_state(config)
                if "human_review" in snapshot.next:
                    await self.store.waiting_review(
                        task_id, snapshot.config["configurable"]["checkpoint_id"]
                    )
            await self.store.finish_command(command)
        except (AgentError, ModelError, AnalysisError, KnowledgeOperationError) as exc:
            recoverable = exc.code in {
                "MODEL_TIMEOUT",
                "MODEL_HTTP_ERROR",
                "MODEL_CALL_AMBIGUOUS",
                "DEPENDENCY_UNAVAILABLE",
            }
            await self.store.fail(task_id, exc.code, recoverable=recoverable)
            await self.store.finish_command(command, exc.code)
        except (DatabaseError, PoolTimeout):
            raise
        except Exception:
            await self.store.fail(task_id, "INTERNAL_ERROR", recoverable=False)
            await self.store.finish_command(command, "INTERNAL_ERROR")


async def reconcile_workspace(store):
    for task in store.list():
        if task.get("schemaVersion") != 1 or task["status"] not in {
            "queued",
            "running",
            "resuming",
        }:
            continue
        commands = [
            c
            for c in store.commands.values()
            if c["taskId"] == task["id"] and c["status"] == "pending"
        ]
        if any(c["status"] == "reserved" for c in task["_agent"]["calls"].values()):
            await store.fail(task["id"], "MODEL_CALL_AMBIGUOUS", recoverable=True)
            for command in commands:
                await store.finish_command(command, "MODEL_CALL_AMBIGUOUS")
        elif not commands:
            await store.fail(task["id"], "RECOVERY_REQUIRED", recoverable=True)

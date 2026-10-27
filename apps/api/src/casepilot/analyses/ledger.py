"""Persist bounded call attempts in task JSONB before external side effects."""

import json
from copy import deepcopy
from datetime import datetime, timezone

from ..model.errors import ModelError
from .agent_errors import AgentError


class TaskLedger:
    def __init__(self, store, task_id):
        self.store, self.task_id = store, task_id

    async def _change(self, update):
        async with self.store.lock:
            task = self.store.get(self.task_id)
            result = update(task)
            if self.store.repository:
                await self.store.repository.save(task)
            self.store.tasks[self.task_id] = task
            return deepcopy(result)

    async def initialize(self, context):
        def update(task):
            if "_agent" in task:
                if task["_agent"]["context"] != context:
                    raise AgentError("AGENT_CONTEXT_CONFLICT")
            else:
                task["_agent"] = {
                    "context": deepcopy(context),
                    "calls": {},
                    "counts": {"model": 0, "retrieval": 0, "repair": 0},
                }
            return task["_agent"]

        return await self._change(update)

    async def run(self, key, kind, operation, *, reserve_model=3, repair=False, attempt=None):
        if attempt is None:
            attempt = self.store.get(self.task_id).get("_agent", {}).get("attempts", {}).get(key, 1)
        if (
            not isinstance(key, str)
            or not 1 <= len(key) <= 200
            or kind not in {"model", "retrieval", "local"}
            or type(attempt) is not int
            or attempt < 1
            or type(reserve_model) is not int
            or not 0 <= reserve_model <= 8
            or type(repair) is not bool
            or (repair and kind != "model")
        ):
            raise AgentError("CALL_REQUEST_INVALID")
        call_key = f"{key}:{attempt}"

        def reserve(task):
            agent = task["_agent"]
            existing = agent["calls"].get(call_key)
            if existing:
                if existing["kind"] != kind or existing["repair"] != repair:
                    raise AgentError("CALL_INTENT_CONFLICT")
                if existing["status"] == "completed":
                    return {"cached": True, "result": existing["result"]}
                raise AgentError(existing.get("error", "MODEL_CALL_AMBIGUOUS"))
            # Retries require an explicit new attempt and still consume the global budget.
            if attempt > 1 and f"{key}:{attempt - 1}" not in agent["calls"]:
                raise AgentError("CALL_ATTEMPT_INVALID")
            if attempt > 1 and agent["calls"][f"{key}:{attempt - 1}"]["status"] == "completed":
                raise AgentError("CALL_ATTEMPT_INVALID")
            counts = agent["counts"]
            if kind == "model" and counts["model"] + 1 + reserve_model > 8:
                raise AgentError("MODEL_BUDGET_EXHAUSTED")
            if kind == "retrieval" and counts["retrieval"] >= 3:
                raise AgentError("RETRIEVAL_BUDGET_EXHAUSTED")
            first_repair = repair and not any(k.rsplit(":", 1)[0] == key for k in agent["calls"])
            if first_repair and counts["repair"] >= 1:
                raise AgentError("STRUCTURE_REPAIR_EXHAUSTED")
            if kind in counts:
                counts[kind] += 1
            if first_repair:
                counts["repair"] += 1
            agent["calls"][call_key] = {
                "kind": kind,
                "repair": repair,
                "status": "reserved",
                "startedAt": datetime.now(timezone.utc).isoformat(),
            }
            if projector := getattr(self.store, "project_agent_call", None):
                projector(task, call_key, agent["calls"][call_key])
            return {"cached": False}

        reservation = await self._change(reserve)
        if reservation["cached"]:
            return reservation["result"]
        try:
            result = await operation()
            json.dumps(result, ensure_ascii=False, allow_nan=False)
        except Exception as exc:
            # Unknown exceptions retain a safe code, never arbitrary provider messages.
            safe_code = exc.code if isinstance(exc, (AgentError, ModelError)) else "CALL_FAILED"

            def fail(task):
                task["_agent"]["calls"][call_key].update(status="failed", error=safe_code)
                if projector := getattr(self.store, "project_agent_call", None):
                    projector(task, call_key, task["_agent"]["calls"][call_key])

            await self._change(fail)
            raise

        def commit(task):
            task["_agent"]["calls"][call_key].update(status="completed", result=deepcopy(result))
            if projector := getattr(self.store, "project_agent_call", None):
                projector(task, call_key, task["_agent"]["calls"][call_key])
            return result

        return await self._change(commit)

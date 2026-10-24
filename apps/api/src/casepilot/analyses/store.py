"""Task projection, lifecycle and local locks; persistence is delegated."""

import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from ..persistence.analysis_repository import PostgresAnalysisRepository
from ..persistence.identifiers import identifier
from .errors import AnalysisError


class Store:
    def __init__(self, pool=None, schema="casepilot_python"):
        self.pool = pool
        self.schema = identifier(schema)
        self.tasks = {}
        self.commands = {}
        self.lock = asyncio.Lock()
        self.repository = PostgresAnalysisRepository(pool, self.schema) if pool else None

    async def setup(self):
        if self.repository:
            self.tasks, self.commands = await self.repository.load()

    def get(self, task_id):
        if task_id not in self.tasks:
            raise AnalysisError("ANALYSIS_NOT_FOUND", f"Analysis task {task_id} not found")
        return deepcopy(self.tasks[task_id])

    def list(self):
        return sorted(
            deepcopy(list(self.tasks.values())), key=lambda t: t["events"][0]["at"], reverse=True
        )

    async def mutate(self, task_id, patch=None, event=None, key=None):
        async with self.lock:
            task = self.get(task_id)
            # Stable node keys prevent duplicated side effects on checkpoint replay.
            if key and key in task.get("_effects", []):
                return task
            task.update(patch or {})
            if event:
                kind, title, detail, data = event
                entry = {
                    "id": len(task["events"]) + 1,
                    "type": kind,
                    "at": datetime.now(timezone.utc)
                    .isoformat(timespec="milliseconds")
                    .replace("+00:00", "Z"),
                    "title": title,
                    "status": task["status"],
                }
                if detail is not None:
                    entry["detail"] = detail
                if data is not None:
                    entry["data"] = data
                task["events"].append(entry)
            if key:
                task.setdefault("_effects", []).append(key)
            if self.repository:
                await self.repository.save(task)
            self.tasks[task_id] = task
            return deepcopy(task)

    async def create(self, case_id):
        task_id = str(uuid4())
        task = {
            "id": task_id,
            "caseId": case_id,
            "status": "running",
            "events": [
                {
                    "id": 1,
                    "type": "status",
                    "at": datetime.now(timezone.utc)
                    .isoformat(timespec="milliseconds")
                    .replace("+00:00", "Z"),
                    "title": "分析任务已创建",
                    "detail": f"案件 {case_id}",
                    "status": "running",
                }
            ],
            "findings": [],
            "citations": [],
            "_effects": ["created"],
        }
        command = {"id": str(uuid4()), "taskId": task_id, "kind": "start", "status": "pending"}
        async with self.lock:
            if self.repository:
                await self.repository.save_with_command(task, command)
            self.tasks[task_id] = task
            self.commands[command["id"]] = command
        return self.get(task_id)

    async def enqueue(self, task_id, payload):
        command = {"id": str(uuid4()), "taskId": task_id, **payload, "status": "pending"}
        if self.repository:
            await self.repository.enqueue(command)
        self.commands[command["id"]] = command
        return command

    async def accept_review(self, task_id, review):
        async with self.lock:
            task = self.get(task_id)
            if task["status"] != "waiting_review":
                raise AnalysisError("REVIEW_CONFLICT", "只有等待审核的任务可以提交审核。")
            task.update(status="running", review=review)
            command = {
                "id": str(uuid4()),
                "taskId": task_id,
                "kind": "review",
                "review": review,
                "status": "pending",
            }
            if self.repository:
                await self.repository.save_with_command(task, command)
            self.tasks[task_id] = task
            self.commands[command["id"]] = command
        return command

    async def finish_command(self, command, error=None):
        if self.repository:
            await self.repository.finish_command(command["id"], error)
        command["status"] = "done"

    @staticmethod
    def public(task):
        return {k: v for k, v in task.items() if not k.startswith("_")}

"""Atomic checkpoints for safely resuming one evaluation output and schema."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from .budget import write_json


def _now():
    return datetime.now(timezone.utc).isoformat()


class RunStateError(RuntimeError):
    pass


class RunState:
    VERSION = 1

    def __init__(self, path, data):
        self.path = Path(path)
        self.data = data

    @classmethod
    def create(
        cls,
        path,
        *,
        schema,
        checkpoint_schema,
        run_id,
        fingerprint,
        budget_ledger,
    ):
        path = Path(path)
        if path.exists():
            raise RunStateError("EVALUATION_STATE_ALREADY_EXISTS")
        timestamp = _now()
        state = cls(
            path,
            {
                "version": cls.VERSION,
                "runId": run_id,
                "schema": schema,
                "checkpointSchema": checkpoint_schema,
                "sourceFingerprint": fingerprint,
                "budgetLedger": str(Path(budget_ledger).resolve()),
                "createdAt": timestamp,
                "updatedAt": timestamp,
                "completed": {"indexes": {}, "reports": {}},
                "inProgress": None,
            },
        )
        state._save()
        return state

    @classmethod
    def resume(cls, path, *, fingerprint, budget_ledger):
        path = Path(path)
        try:
            data = __import__("json").loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError):
            raise RunStateError("EVALUATION_STATE_INVALID") from None
        if (
            not isinstance(data, dict)
            or data.get("version") != cls.VERSION
            or not all(
                isinstance(data.get(field), str) and data[field]
                for field in (
                    "runId",
                    "schema",
                    "checkpointSchema",
                    "sourceFingerprint",
                    "budgetLedger",
                )
            )
            or not isinstance(data.get("completed"), dict)
            or "inProgress" not in data
        ):
            raise RunStateError("EVALUATION_STATE_INVALID")
        if data["sourceFingerprint"] != fingerprint:
            raise RunStateError("EVALUATION_SOURCE_CHANGED")
        if Path(data["budgetLedger"]).resolve() != Path(budget_ledger).resolve():
            raise RunStateError("EVALUATION_BUDGET_LEDGER_CHANGED")
        if data["inProgress"] is not None:
            raise RunStateError("EVALUATION_STAGE_IN_PROGRESS")
        return cls(path, data)

    @property
    def run_id(self):
        return self.data["runId"]

    @property
    def schema(self):
        return self.data["schema"]

    @property
    def checkpoint_schema(self):
        return self.data["checkpointSchema"]

    @property
    def in_progress(self):
        return deepcopy(self.data["inProgress"])

    def _save(self):
        self.data["updatedAt"] = _now()
        write_json(self.path, self.data)

    def is_complete(self, stage, item=None):
        if item is None:
            return stage in self.data["completed"]
        return item in self.data["completed"].get(stage, {})

    def value(self, stage, item=None):
        if item is None:
            return deepcopy(self.data["completed"].get(stage))
        return deepcopy(self.data["completed"].get(stage, {}).get(item))

    def begin(self, stage, *, item=None, data=None):
        expected = {"stage": stage, "item": item, "data": deepcopy(data) if data else {}}
        active = self.data["inProgress"]
        if active is not None:
            if active["stage"] != stage or active.get("item") != item:
                raise RunStateError("EVALUATION_STAGE_IN_PROGRESS")
            return deepcopy(active)
        self.data["inProgress"] = expected
        self._save()
        return deepcopy(expected)

    def progress(self, patch):
        if self.data["inProgress"] is None:
            raise RunStateError("EVALUATION_STAGE_NOT_STARTED")
        self.data["inProgress"]["data"].update(deepcopy(patch))
        self._save()
        return self.in_progress

    def complete(self, stage, value, *, item=None):
        active = self.data["inProgress"]
        if active is not None and (
            active["stage"] != stage or active.get("item") != item
        ):
            raise RunStateError("EVALUATION_STAGE_IN_PROGRESS")
        if item is None:
            self.data["completed"][stage] = deepcopy(value)
        else:
            self.data["completed"].setdefault(stage, {})[item] = deepcopy(value)
        self.data["inProgress"] = None
        self._save()


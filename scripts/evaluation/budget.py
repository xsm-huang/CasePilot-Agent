"""Shared provider budget with durable pre-reservation and fail-stop semantics."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
from casepilot.model.errors import ModelError


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


@contextmanager
def _file_lock(path):
    """Lock one byte in a sibling file so separate runs share one counter safely."""

    lock_path = Path(str(path) + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class BudgetLedger:
    """The single durable authority for all live runs under one approved cap."""

    def __init__(
        self,
        path,
        model_limit,
        embedding_limit,
        *,
        run_id="unspecified",
        initial_used=None,
    ):
        self.path = Path(path).resolve()
        self.limits = {"model": model_limit, "embedding": embedding_limit}
        self.run_id = run_id
        self.initial_used = initial_used or {"model": 0, "embedding": 0}
        if (
            set(self.initial_used) != set(self.limits)
            or any(
                type(self.initial_used[kind]) is not int
                or not 0 <= self.initial_used[kind] <= self.limits[kind]
                for kind in self.limits
            )
        ):
            raise ValueError("Initial shared budget usage is invalid")
        self.lock = threading.Lock()
        with self._locked() as state:
            if state["limits"] != self.limits:
                raise ValueError("Existing shared budget limits cannot change")
            if any(call.get("status") == "reserved" for call in state["calls"]):
                state["stopped"] = state["stopped"] or "AMBIGUOUS_PROVIDER_CALL"

    def _read(self):
        if not self.path.exists():
            return {
                "version": 2,
                "limits": self.limits,
                "used": dict(self.initial_used),
                "migratedUsed": dict(self.initial_used),
                "stopped": None,
                "calls": [],
            }
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
            if (
                not isinstance(state, dict)
                or not isinstance(state.get("limits"), dict)
                or not isinstance(state.get("used"), dict)
                or not isinstance(state.get("calls"), list)
                or "stopped" not in state
            ):
                raise ValueError()
            return state
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            raise ValueError("Shared budget ledger is invalid") from None

    @contextmanager
    def _locked(self):
        with self.lock, _file_lock(self.path):
            state = self._read()
            try:
                yield state
            finally:
                write_json(self.path, state)

    @property
    def state(self):
        with self.lock, _file_lock(self.path):
            return self._read()

    def ensure_active(self):
        state = self.state
        if state["stopped"]:
            raise ModelError("EVALUATION_STOPPED")
        return state

    def reserve(self, kind, model):
        if kind not in self.limits:
            raise ModelError("EVALUATION_REQUEST_INVALID")
        with self._locked() as state:
            if state["stopped"]:
                raise ModelError("EVALUATION_STOPPED")
            if state["used"][kind] >= state["limits"][kind]:
                state["stopped"] = "EVALUATION_BUDGET_EXHAUSTED"
                raise ModelError("EVALUATION_BUDGET_EXHAUSTED")
            state["used"][kind] += 1
            entry = {
                "id": str(uuid4()),
                "runId": self.run_id,
                "kind": kind,
                "model": model,
                "status": "reserved",
                "at": datetime.now(timezone.utc).isoformat(),
            }
            state["calls"].append(entry)
            return entry

    def finish(self, entry, patch, stop=None):
        with self._locked() as state:
            stored = next((call for call in state["calls"] if call.get("id") == entry["id"]), None)
            if stored is None or stored.get("status") != "reserved":
                state["stopped"] = state["stopped"] or "AMBIGUOUS_PROVIDER_CALL"
                raise ModelError("EVALUATION_STOPPED")
            stored.update(patch)
            if stop:
                state["stopped"] = state["stopped"] or stop

    def stop(self, reason):
        with self._locked() as state:
            state["stopped"] = state["stopped"] or reason
            return state


class BudgetTransport(httpx.AsyncBaseTransport):
    def __init__(
        self, path, model_limit, embedding_limit, *, run_id="unspecified", transport=None
    ):
        self.transport = transport or httpx.AsyncHTTPTransport(retries=0)
        self.ledger = BudgetLedger(path, model_limit, embedding_limit, run_id=run_id)
        # Compatibility for the evaluation server and earlier focused tests.
        self.path = self.ledger.path
        self.lock = self.ledger.lock

    @property
    def state(self):
        return self.ledger.state

    def reserve(self, kind, model):
        return self.ledger.reserve(kind, model)

    def finish(self, entry, patch, stop=None):
        return self.ledger.finish(entry, patch, stop)

    def stop(self, reason):
        return self.ledger.stop(reason)

    async def handle_async_request(self, request):
        kind = (
            "model"
            if request.url.path.endswith("/chat/completions")
            else "embedding"
            if request.url.path.endswith("/embeddings")
            else None
        )
        if kind is None:
            raise ModelError("EVALUATION_REQUEST_INVALID")
        body = json.loads(request.content)
        entry = self.reserve(kind, body["model"])
        start = time.monotonic()
        try:
            response = await self.transport.handle_async_request(request)
            await response.aread()
            try:
                data = response.json()
            except ValueError:
                data = {}
            error = data.get("error", {}) if isinstance(data, dict) else {}
            raw_code = str(error.get("code", "")) if isinstance(error, dict) else ""
            code = raw_code if re.fullmatch(r"[0-9]{1,8}", raw_code) else None
            usage = data.get("usage", {}) if isinstance(data, dict) else {}
            safe_usage = (
                {
                    key: value
                    for key, value in usage.items()
                    if key in {"prompt_tokens", "completion_tokens", "total_tokens"}
                    and type(value) is int
                    and value >= 0
                }
                if isinstance(usage, dict)
                else {}
            )
            failed = response.status_code != 200 or bool(error)
            self.finish(
                entry,
                {
                    "status": "failed" if failed else "completed",
                    "httpStatus": response.status_code,
                    "providerCode": code,
                    "usage": safe_usage,
                    "durationMs": int((time.monotonic() - start) * 1000),
                },
                "PROVIDER_REQUEST_FAILED" if failed else None,
            )
            return response
        except Exception as exc:
            # A provider response failure was already durably finalized above.
            current = self.state
            stored = next(
                (call for call in current["calls"] if call.get("id") == entry["id"]), None
            )
            if stored and stored.get("status") == "reserved":
                self.finish(
                    entry,
                    {
                        "status": "ambiguous",
                        "errorType": type(exc).__name__,
                        "durationMs": int((time.monotonic() - start) * 1000),
                    },
                    "PROVIDER_REQUEST_INTERRUPTED",
                )
            raise

    async def aclose(self):
        await self.transport.aclose()

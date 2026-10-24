"""Independent HTTP acceptance harness; no in-process ASGI buffering."""

from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
import pytest
from psycopg import sql

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps/api/src"))


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ApiProcess:
    def __init__(self, extra_env=None):
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}/api"
        self.extra_env = extra_env or {}
        self.process = None
        self.log = tempfile.TemporaryFile(mode="w+b")

    def diagnostics(self):
        self.log.seek(0)
        content = self.log.read().decode("utf-8", errors="replace")
        for key, value in self.extra_env.items():
            if value and ("URL" in key or "KEY" in key or "PASSWORD" in key):
                content = content.replace(value, "[redacted]")
        return content[-6000:]

    def start(self):
        env = os.environ.copy()
        env.update(self.extra_env)
        # Migration acceptance is deterministic and must not use real credentials.
        for name in list(env):
            if name.endswith("API_KEY"):
                env[name] = ""
        env["ZHIPU_API_KEY"] = ""
        env["OPENAI_API_KEY"] = ""
        env["PORT"] = str(self.port)
        env["HOST"] = "127.0.0.1"
        env["PYTHONPATH"] = str(ROOT / "apps/api/src")
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "casepilot",
            ],
            cwd=ROOT,
            env=env,
            stdout=self.log,
            stderr=self.log,
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise AssertionError(
                    f"API subprocess exited {self.process.returncode}: {self.diagnostics()}"
                )
            try:
                if httpx.get(f"{self.base}/cases", timeout=0.5).status_code == 200:
                    return self
            except httpx.HTTPError:
                pass
            time.sleep(0.05)
        self.stop()
        raise AssertionError(f"API subprocess startup exceeded 30 seconds: {self.diagnostics()}")

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)


@pytest.fixture(scope="session")
def api_process():
    server = ApiProcess({"CASEPILOT_STORAGE": "memory"}).start()
    yield server
    server.stop()


@pytest.fixture
def api(api_process):
    with httpx.Client(base_url=api_process.base, timeout=5) as client:
        yield client


def create_settled(api, case_id="CASE-2026-001"):
    response = api.post("/analyses", json={"caseId": case_id})
    assert response.status_code in (200, 201), response.text
    task_id = response.json()["id"]
    return settle_task(api, task_id)


def settle_task(api, task_id):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        response = api.get(f"/analyses/{task_id}")
        response.raise_for_status()
        task = response.json()
        if task["status"] != "running":
            return task
        time.sleep(0.02)
    raise AssertionError(f"Task {task_id} did not settle")


def sse_events(response):
    payload = []
    event_id = None
    for line in response.iter_lines():
        if line.startswith("id:"):
            event_id = int(line[3:].strip())
        elif line.startswith("data:"):
            payload.append(line[5:].lstrip())
        elif not line and payload:
            import json

            value = json.loads("\n".join(payload))
            assert event_id == value["id"]
            yield value
            payload = []
            event_id = None


@pytest.fixture
def postgres_env():
    database_url = os.environ.get("CASEPILOT_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Database integration not executed: set CASEPILOT_TEST_DATABASE_URL")
    schema = f"casepilot_test_{uuid4().hex}"
    checkpoint_schema = schema + "_cp"
    owned = (schema, checkpoint_schema)
    env = {
        "CASEPILOT_STORAGE": "postgres",
        "DATABASE_URL": database_url,
        "CASEPILOT_DB_SCHEMA": schema,
        "CASEPILOT_CHECKPOINT_SCHEMA": checkpoint_schema,
    }
    try:
        yield env
    finally:
        # Identifiers come solely from this fixture, never user-supplied names.
        assert all(re.fullmatch(r"casepilot_test_[0-9a-f]{32}(?:_cp)?", name) for name in owned)
        with psycopg.connect(database_url, autocommit=True) as conn:
            for name in reversed(owned):
                conn.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(name))
                )

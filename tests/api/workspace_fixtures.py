"""Workspace model substitute; never enabled by production environment flags."""

import asyncio
import json
import threading
import time
from uuid import uuid4

import pytest
from casepilot.main import create_app
from casepilot.model.config import read_model_config
from casepilot.model.errors import ModelError
from fastapi.testclient import TestClient
from pdf_fixtures import text_pdf
from test_knowledge_database import FakeEmbedding


class WorkspaceChat:
    def __init__(self):
        self.config = read_model_config({"ZHIPU_API_KEY": "test-no-network"})
        self.calls = []
        self.fail_section = None
        self.failed = False
        self.block_section = None
        self.invalid_section = None
        self.release = threading.Event()

    async def complete(self, messages, *, tools=None, json_mode=False):
        payload = json.loads(messages[1]["content"])
        section = payload.get("sectionKey")
        self.calls.append({"section": section, "tools": bool(tools), "payload": payload})
        if section == self.block_section and section is not None:
            await asyncio.to_thread(self.release.wait, 15)
        if section == self.fail_section and section is not None and not self.failed:
            self.failed = True
            raise ModelError("MODEL_TIMEOUT")
        if tools:
            output = "已有依据，进入结构化分析。"
        elif section:
            citations = payload["analysis"]["citations"]
            output = {
                "content": f"{section}：基于已核查的事实与条款，保留疑点并建议人工复核。",
                "factRefs": ["case:accidentDate"],
                "citationRefs": [citations[0]["citationId"]] if citations else [],
            }
            if section == self.invalid_section:
                output["citationRefs"] = ["not-in-task"]
        else:
            output = {
                "summary": "已核查事实与条款。",
                "findings": [],
                "insufficientEvidence": not bool(payload["citations"]),
                "pendingItems": [],
            }
        return {
            "content": output
            if isinstance(output, str)
            else json.dumps(output, ensure_ascii=False),
            "toolCalls": [],
            "usage": {"total_tokens": 10},
        }


def settle(client, task_id, expected=None):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        response = client.get(f"/api/analyses/{task_id}")
        assert response.status_code == 200, response.text
        task = response.json()
        if task["status"] not in {"queued", "running", "resuming"}:
            if expected:
                assert task["status"] == expected, task
            return task
        time.sleep(0.03)
    raise AssertionError(f"Task did not settle: {task_id}")


def new_task(client, case_id="CASE-2026-002"):
    response = client.post(f"/api/cases/{case_id}/conversations", json={"title": "验收会话"})
    assert response.status_code == 201, response.text
    conversation = response.json()
    response = client.post(
        "/api/analyses",
        json={"conversationId": conversation["id"], "kind": "initial"},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 202, response.text
    return conversation, response.json()


def seed_knowledge(client):
    response = client.post(
        "/api/knowledge/documents",
        data={"productCode": "AUTO-COMPREHENSIVE", "clauseVersion": "2025-01"},
        files={
            "file": (
                "验收条款.pdf",
                text_pdf(["Repair invoice and accident evidence must be reviewed."]),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 202, response.text
    generation_id = response.json()["generationId"]
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        generation = client.get(f"/api/knowledge/generations/{generation_id}").json()
        if generation["status"] == "ready":
            return generation
        assert generation["status"] != "failed", generation
        time.sleep(0.03)
    raise AssertionError("Test index did not finish")


@pytest.fixture
def workspace(postgres_env, monkeypatch):
    for key, value in postgres_env.items():
        monkeypatch.setenv(key, value)
    chat = WorkspaceChat()
    application = create_app(chat=chat, embedder=FakeEmbedding())
    options = (
        {"loop_factory": asyncio.SelectorEventLoop} if hasattr(asyncio, "SelectorEventLoop") else {}
    )
    with TestClient(application, backend_options=options) as client:
        seed_knowledge(client)
        yield client, application, chat

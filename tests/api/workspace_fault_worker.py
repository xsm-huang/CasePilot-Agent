"""Test-only barriers around actual production persistence/checkpoint boundaries."""

import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from casepilot.main import create_app
from test_knowledge_database import FakeEmbedding
from workspace_fixtures import WorkspaceChat

stage = os.environ["WORKSPACE_FAULT_STAGE"]
marker = Path(os.environ["WORKSPACE_FAULT_MARKER"])
chat = WorkspaceChat()
app = create_app(chat=chat, embedder=FakeEmbedding())
production_lifespan = app.router.lifespan_context


async def barrier(task_id):
    marker.write_text(task_id, encoding="utf-8")
    await asyncio.Event().wait()


@asynccontextmanager
async def lifespan(application):
    async with production_lifespan(application):
        store = application.state.store
        commit = store.repository.commit
        section = store.section
        waiting = store.waiting_review
        complete = chat.complete

        async def commit_wrapper(task, **kwargs):
            await commit(task, **kwargs)
            if stage == "review_accepted" and kwargs.get("review"):
                await barrier(task["id"])

        async def section_wrapper(task_id, key, output):
            result = await section(task_id, key, output)
            if stage == "section_committed" and key == "summary":
                await barrier(task_id)
            return result

        async def waiting_wrapper(task_id, checkpoint_id):
            if stage == "checkpoint_before_projection":
                await barrier(task_id)
            return await waiting(task_id, checkpoint_id)

        async def complete_wrapper(messages, **kwargs):
            result = await complete(messages, **kwargs)
            if (
                stage == "model_returned"
                and json.loads(messages[1]["content"]).get("sectionKey") == "summary"
            ):
                task = next(t for t in store.tasks.values() if t["status"] == "running")
                await barrier(task["id"])
            return result

        store.repository.commit = commit_wrapper
        store.section = section_wrapper
        store.waiting_review = waiting_wrapper
        chat.complete = complete_wrapper
        yield


app.router.lifespan_context = lifespan
server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=int(os.environ["PORT"])))
if sys.platform == "win32":
    asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)
else:
    asyncio.run(server.serve())

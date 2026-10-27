"""Explicit test-only server composition; production never selects fake providers."""

import asyncio
import os
import sys

import uvicorn
from casepilot.main import create_app
from test_knowledge_database import FakeEmbedding
from workspace_fixtures import WorkspaceChat

app = create_app(chat=WorkspaceChat(), embedder=FakeEmbedding())
server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=int(os.environ["PORT"])))
if sys.platform == "win32":
    asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)
else:
    asyncio.run(server.serve())

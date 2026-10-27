"""Application resource composition and background-task lifecycle."""

import asyncio
import os
from contextlib import AsyncExitStack, asynccontextmanager

from .analyses.worker import run_commands
from .analyses.workspace_executor import WorkspaceExecutor, reconcile_workspace
from .analyses.workspace_service import WorkspaceService
from .analyses.workspace_store import WorkspaceStore
from .knowledge.repository import PostgresKnowledgeRepository
from .knowledge.service import KnowledgeService
from .model import embed_texts, read_model_config
from .persistence.runtime import open_storage
from .workflow.workspace_graph import create_workspace_graph


@asynccontextmanager
async def lifespan(app):
    async with AsyncExitStack() as stack:
        pool, checkpointer = await open_storage(stack)
        store = WorkspaceStore(pool, os.getenv("CASEPILOT_DB_SCHEMA", "casepilot_python"))
        await store.setup()
        app.state.store = store
        wakeup = asyncio.Event()
        app.state.wakeup = wakeup
        app.state.knowledge = None
        knowledge_worker = None
        if pool:
            repository = PostgresKnowledgeRepository(pool, store.schema)
            await repository.setup()
            await repository.reconcile()

            async def production_embeddings(texts):
                return await embed_texts(read_model_config(), texts)

            knowledge = KnowledgeService(
                repository, app.state.embedding_adapter or production_embeddings
            )
            app.state.knowledge = knowledge

        service = WorkspaceService(store, wakeup, app.state.knowledge, app.state.chat_adapter)
        app.state.analyses = service
        executor = WorkspaceExecutor(
            store, create_workspace_graph(store, app.state.knowledge, service.chat, checkpointer)
        )
        app.state.executor = executor
        await reconcile_workspace(store)

        worker = asyncio.create_task(run_commands(store, executor, wakeup))
        try:
            if app.state.knowledge:
                knowledge_worker = asyncio.create_task(app.state.knowledge.run())
            yield
        finally:
            if knowledge_worker:
                knowledge_worker.cancel()
                try:
                    await knowledge_worker
                except asyncio.CancelledError:
                    pass
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass

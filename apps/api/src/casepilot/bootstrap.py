"""Application resource composition and background-task lifecycle."""

import asyncio
import os
from contextlib import AsyncExitStack, asynccontextmanager

from .analyses.executor import Executor
from .analyses.service import AnalysisService
from .analyses.store import Store
from .analyses.worker import reconcile_commands, run_commands
from .knowledge.repository import PostgresKnowledgeRepository
from .knowledge.service import KnowledgeService
from .model import embed_texts, read_model_config
from .persistence.runtime import open_storage
from .workflow.graph import create_graph


@asynccontextmanager
async def lifespan(app):
    async with AsyncExitStack() as stack:
        pool, checkpointer = await open_storage(stack)
        store = Store(pool, os.getenv("CASEPILOT_DB_SCHEMA", "casepilot_python"))
        await store.setup()
        executor = Executor(store, create_graph(store, checkpointer))
        app.state.store = store
        app.state.executor = executor
        wakeup = asyncio.Event()
        app.state.wakeup = wakeup
        app.state.analyses = AnalysisService(store, wakeup)
        app.state.knowledge = None
        knowledge_worker = None
        if pool:
            repository = PostgresKnowledgeRepository(pool, store.schema)
            await repository.setup()
            await repository.reconcile()

            async def production_embeddings(texts):
                return await embed_texts(read_model_config(), texts)

            knowledge = KnowledgeService(repository, production_embeddings)
            app.state.knowledge = knowledge

        await reconcile_commands(store)

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

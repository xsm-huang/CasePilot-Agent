"""Test-only component process with a durable phase barrier; no HTTP test route."""

import asyncio
import os
import sys
from pathlib import Path

from casepilot.knowledge.repository import PostgresKnowledgeRepository
from casepilot.knowledge.service import KnowledgeService
from psycopg_pool import AsyncConnectionPool


async def work(stage, marker):
    async with AsyncConnectionPool(os.environ["DATABASE_URL"], open=False) as pool:
        await pool.wait()
        repo = PostgresKnowledgeRepository(pool, os.environ["CASEPILOT_DB_SCHEMA"])
        await repo.setup()
        original_update = repo.update

        async def update(generation_id, **patch):
            await original_update(generation_id, **patch)
            if patch.get("status") == stage:
                Path(marker).write_text(generation_id, encoding="utf-8")
                await asyncio.Event().wait()

        repo.update = update

        async def embedder(texts):
            return [[0.25] * 1024 for _ in texts]

        service = KnowledgeService(repo, embedder)
        await service.process_next()


if __name__ == "__main__":
    task = work(sys.argv[1], sys.argv[2])
    if sys.platform == "win32":
        asyncio.run(task, loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(task)

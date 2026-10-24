"""Acquire pools, a single-worker lock and official checkpoint resources."""

import os

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection, sql
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from .identifiers import identifier


async def open_storage(stack):
    mode = os.getenv("CASEPILOT_STORAGE", "memory")
    if mode not in {"memory", "postgres"}:
        raise ValueError("CASEPILOT_STORAGE must be memory or postgres")
    pool = None
    checkpointer = InMemorySaver()
    if mode == "postgres":
        url = os.environ["DATABASE_URL"]
        pool = await stack.enter_async_context(AsyncConnectionPool(url, open=False))
        await pool.wait()
        cp_schema = identifier(
            os.getenv("CASEPILOT_CHECKPOINT_SCHEMA", "casepilot_python_checkpoint")
        )
        conn = await stack.enter_async_context(
            await AsyncConnection.connect(
                url, autocommit=True, row_factory=dict_row, prepare_threshold=0
            )
        )
        # The executor owns an in-memory projection of persisted snapshots.
        # Fail loudly if a second process targets the same application schema.
        app_schema = identifier(os.getenv("CASEPILOT_DB_SCHEMA", "casepilot_python"))
        lock_result = await conn.execute(
            "SELECT pg_try_advisory_lock(hashtextextended(%s, 0)) AS acquired",
            (f"casepilot-python:{app_schema}",),
        )
        if not (await lock_result.fetchone())["acquired"]:
            raise RuntimeError("CasePilot requires one API worker per application schema")
        await conn.execute(
            sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(cp_schema))
        )
        await conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(cp_schema)))
        checkpointer = AsyncPostgresSaver(conn)
        await checkpointer.setup()

    return pool, checkpointer

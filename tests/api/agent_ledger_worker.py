"""Independent process used only for durable G3 accounting tests."""

import asyncio
import json
import os
import sys
from pathlib import Path

from casepilot.analyses.agent_errors import AgentError
from casepilot.analyses.ledger import TaskLedger
from casepilot.analyses.store import Store
from psycopg_pool import AsyncConnectionPool


async def main():
    mode = sys.argv[1]
    async with AsyncConnectionPool(os.environ["DATABASE_URL"], open=False) as pool:
        await pool.wait()
        store = Store(pool, os.environ["CASEPILOT_DB_SCHEMA"])
        await store.setup()
        task_id = (await store.create("CASE-2026-002"))["id"] if mode == "seed" else sys.argv[2]
        ledger = TaskLedger(store, task_id)
        await ledger.initialize({"generationId": "fixed-generation"})

        async def effect():
            return {"assessment": "committed"}

        if mode == "seed":
            await ledger.run("analysis", "model", effect)
            print(json.dumps({"taskId": task_id}), flush=True)
        elif mode == "replay":

            async def forbidden():
                raise AssertionError("Committed external effect was repeated")

            assert await ledger.run("analysis", "model", forbidden) == {"assessment": "committed"}
            print(
                json.dumps({"count": store.get(task_id)["_agent"]["counts"]["model"]}), flush=True
            )
        elif mode == "interrupt":

            async def ambiguous():
                Path(sys.argv[3]).write_text("reserved", encoding="utf-8")
                await asyncio.Event().wait()

            await ledger.run("ambiguous", "model", ambiguous)
        elif mode == "recover":
            try:
                await ledger.run("ambiguous", "model", effect)
            except AgentError as exc:
                assert exc.code == "MODEL_CALL_AMBIGUOUS"
            else:
                raise AssertionError("An ambiguous external call was silently replayed")
            await ledger.run("ambiguous", "model", effect, attempt=2)
            print(
                json.dumps({"count": store.get(task_id)["_agent"]["counts"]["model"]}), flush=True
            )


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(main())

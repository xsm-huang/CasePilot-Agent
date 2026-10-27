"""Restart reconciliation and durable command polling."""

import asyncio
import logging


async def run_commands(store, executor, wakeup):
    while True:
        pending = [c for c in store.commands.values() if c["status"] == "pending"]
        if pending:
            try:
                await executor.execute(pending[0])
            except Exception as exc:
                # A DB outage can prevent persisting even the failure outcome.
                # Keep the durable command pending and the worker alive for retry.
                logging.getLogger(__name__).error(
                    "Command persistence unavailable: %s", type(exc).__name__
                )
                await asyncio.sleep(1)
            continue
        wakeup.clear()
        await wakeup.wait()

"""Supported single-worker launcher, including Psycopg's Windows loop requirement."""

import asyncio
import os
import sys

import uvicorn


def main():
    config = uvicorn.Config(
        "casepilot.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "3000")),
        workers=1,
        loop="asyncio",
    )
    server = uvicorn.Server(config)
    # Uvicorn's Windows loop factory can override the global event loop policy.
    # Own the runner explicitly so PostgreSQL always sees a Selector loop.
    if sys.platform == "win32":
        asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(server.serve())


if __name__ == "__main__":
    main()

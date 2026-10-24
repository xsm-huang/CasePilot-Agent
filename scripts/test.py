"""Opt into isolated database acceptance without exposing the connection string."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", action="store_true", help="Enable real PostgreSQL acceptance")
    args, pytest_args = parser.parse_known_args()
    environment = os.environ.copy()
    if args.database:
        local = dotenv_values(ROOT / ".env")
        target = (
            environment.get("CASEPILOT_TEST_DATABASE_URL")
            or environment.get("DATABASE_URL")
            or local.get("DATABASE_URL")
        )
        if not target:
            parser.error("DATABASE_URL is required for database acceptance")
        environment["CASEPILOT_TEST_DATABASE_URL"] = target
    return subprocess.call(
        [sys.executable, "-m", "pytest", *pytest_args], cwd=ROOT, env=environment
    )


if __name__ == "__main__":
    raise SystemExit(main())

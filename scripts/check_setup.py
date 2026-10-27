"""Read-only local prerequisites; never call a model or print configuration values."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

import psycopg
from casepilot.model.profiles import CHAT_PROFILES
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def configuration_checks(environment: dict[str, str]) -> dict[str, bool]:
    required = (
        "ZHIPU_API_KEY",
        "ZHIPU_BASE_URL",
        "CHAT_MODEL",
        "EMBEDDING_MODEL",
        "EMBEDDING_DIMENSIONS",
        "DATABASE_URL",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_PORT",
    )
    checks = {name: bool(environment.get(name, "").strip()) for name in required}
    checks["CHAT_MODEL_APPROVED"] = environment.get("CHAT_MODEL") in CHAT_PROFILES
    checks["EMBEDDING_MODEL_APPROVED"] = environment.get("EMBEDDING_MODEL") == "embedding-3"
    checks["EMBEDDING_DIMENSIONS_APPROVED"] = environment.get("EMBEDDING_DIMENSIONS") == "1024"
    try:
        port = int(environment.get("POSTGRES_PORT", ""))
        checks["POSTGRES_PORT_VALID"] = 1 <= port <= 65535
    except ValueError:
        checks["POSTGRES_PORT_VALID"] = False
    try:
        url = urlsplit(environment.get("ZHIPU_BASE_URL", ""))
        checks["ZHIPU_BASE_URL_VALID"] = (
            url.scheme == "https"
            and url.netloc == "open.bigmodel.cn"
            and url.path.rstrip("/") == "/api/paas/v4"
            and not url.query
            and not url.fragment
        )
        db = urlsplit(environment.get("DATABASE_URL", ""))
        checks["DATABASE_URL_VALID"] = (
            db.scheme in {"postgres", "postgresql"}
            and db.hostname in {"localhost", "127.0.0.1"}
            and str(db.port) == environment.get("POSTGRES_PORT")
            and unquote(db.username or "") == environment.get("POSTGRES_USER")
            and unquote(db.password or "") == environment.get("POSTGRES_PASSWORD")
            and unquote(db.path.lstrip("/")) == environment.get("POSTGRES_DB")
            and not db.query
            and not db.fragment
        )
    except (ValueError, TypeError):
        checks.setdefault("ZHIPU_BASE_URL_VALID", False)
        checks["DATABASE_URL_VALID"] = False
    return checks


def inspect_setup() -> dict:
    environment = {
        key: value for key, value in dotenv_values(ROOT / ".env").items() if value is not None
    }
    environment.update(os.environ)
    checks = {"ENV_FILE_EXISTS": (ROOT / ".env").is_file(), **configuration_checks(environment)}
    checks.update(DATABASE_AVAILABLE=False, PGVECTOR_AVAILABLE=False)
    if checks["DATABASE_URL_VALID"]:
        try:
            with psycopg.connect(environment["DATABASE_URL"], connect_timeout=5) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    checks["DATABASE_AVAILABLE"] = cursor.fetchone() == (1,)
                    cursor.execute("SELECT '[1,0]'::vector <=> '[1,0]'::vector")
                    value = cursor.fetchone()[0]
                    checks["PGVECTOR_AVAILABLE"] = math.isfinite(value) and value == 0
        except psycopg.Error:
            pass
    return {
        "checks": checks,
        "setupReady": all(checks.values()),
        "providerCapabilitiesVerified": False,
        "checkpointPersistenceVerified": False,
        "g0Passed": False,
    }


if __name__ == "__main__":
    result = inspect_setup()
    print(json.dumps(result, indent=2))
    # A read-only preparation check succeeds when prepared, not when all G0 probes pass.
    raise SystemExit(0 if result["setupReady"] else 1)

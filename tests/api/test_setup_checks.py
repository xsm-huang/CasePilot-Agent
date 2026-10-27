"""Read-only configuration checks: no live model/Embedding calls."""

import importlib.util
import json

import psycopg
import pytest
from conftest import ROOT

spec = importlib.util.spec_from_file_location("setup_checks", ROOT / "scripts/check_setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)

VALID = {
    "ZHIPU_API_KEY": "test-only-never-send",
    "ZHIPU_BASE_URL": "https://open.bigmodel.cn/api/paas/v4",
    "CHAT_MODEL": "glm-5.3-flash",
    "EMBEDDING_MODEL": "embedding-3",
    "EMBEDDING_DIMENSIONS": "1024",
    "POSTGRES_DB": "casepilot",
    "POSTGRES_USER": "casepilot",
    "POSTGRES_PASSWORD": "test-only-password",
    "POSTGRES_PORT": "15432",
    "DATABASE_URL": "postgresql://casepilot:test-only-password@127.0.0.1:15432/casepilot",
}


def test_configuration_is_boolean_and_does_not_expose_credentials():
    assert all(setup.configuration_checks(VALID).values())
    checks = setup.configuration_checks(VALID | {"ZHIPU_API_KEY": " "})
    assert checks["ZHIPU_API_KEY"] is False
    assert all(type(value) is bool for value in checks.values())
    encoded = json.dumps(checks)
    assert VALID["ZHIPU_API_KEY"] not in encoded
    assert VALID["POSTGRES_PASSWORD"] not in encoded


@pytest.mark.parametrize(
    "key,value,check",
    [
        ("CHAT_MODEL", "other", "CHAT_MODEL_APPROVED"),
        ("EMBEDDING_MODEL", "other", "EMBEDDING_MODEL_APPROVED"),
        ("EMBEDDING_DIMENSIONS", "2048", "EMBEDDING_DIMENSIONS_APPROVED"),
        ("ZHIPU_BASE_URL", "https://example.com/api/paas/v4", "ZHIPU_BASE_URL_VALID"),
        ("ZHIPU_BASE_URL", "http://open.bigmodel.cn/api/paas/v4", "ZHIPU_BASE_URL_VALID"),
        ("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4?secret=x", "ZHIPU_BASE_URL_VALID"),
        ("DATABASE_URL", "not-a-url", "DATABASE_URL_VALID"),
        (
            "DATABASE_URL",
            "postgresql://casepilot:test-only-password@evil.example:15432/casepilot",
            "DATABASE_URL_VALID",
        ),
        (
            "DATABASE_URL",
            "postgresql://casepilot:test-only-password@localhost:15432/other",
            "DATABASE_URL_VALID",
        ),
        (
            "DATABASE_URL",
            "postgresql://other:test-only-password@localhost:15432/casepilot",
            "DATABASE_URL_VALID",
        ),
        (
            "DATABASE_URL",
            "postgresql://casepilot:wrong@localhost:15432/casepilot",
            "DATABASE_URL_VALID",
        ),
        ("POSTGRES_PORT", "5432", "DATABASE_URL_VALID"),
        ("POSTGRES_PORT", "0", "POSTGRES_PORT_VALID"),
        ("POSTGRES_PORT", "65536", "POSTGRES_PORT_VALID"),
        ("POSTGRES_PORT", "oops", "POSTGRES_PORT_VALID"),
    ],
)
def test_profile_and_target_boundaries(key, value, check):
    assert setup.configuration_checks(VALID | {key: value})[check] is False


def test_unavailable_database_is_false_and_redacted(monkeypatch):
    monkeypatch.setattr(setup, "dotenv_values", lambda path: {})
    monkeypatch.setattr(setup.os, "environ", VALID)

    def unavailable(*args, **kwargs):
        raise psycopg.OperationalError(VALID["POSTGRES_PASSWORD"])

    monkeypatch.setattr(setup.psycopg, "connect", unavailable)
    result = setup.inspect_setup()
    assert result["checks"]["DATABASE_AVAILABLE"] is False
    assert result["checks"]["PGVECTOR_AVAILABLE"] is False
    assert result["setupReady"] is False
    assert result["providerCapabilitiesVerified"] is False
    assert result["checkpointPersistenceVerified"] is False
    assert VALID["POSTGRES_PASSWORD"] not in json.dumps(result)


def test_invalid_database_does_not_connect(monkeypatch):
    monkeypatch.setattr(setup, "dotenv_values", lambda path: {})
    monkeypatch.setattr(setup.os, "environ", VALID | {"DATABASE_URL": "invalid"})

    def forbidden(*args, **kwargs):
        pytest.fail("Invalid database configuration must not initiate a connection")

    monkeypatch.setattr(setup.psycopg, "connect", forbidden)
    assert setup.inspect_setup()["setupReady"] is False

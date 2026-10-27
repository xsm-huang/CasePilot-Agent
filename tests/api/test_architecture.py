"""Protect dependency boundaries and independently composed application state."""

import ast

from conftest import ROOT

PACKAGE = ROOT / "apps/api/src/casepilot"


def imported_modules(path):
    package = ["casepilot", *path.relative_to(PACKAGE).parts[:-1]]
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = ".".join([*package[: len(package) - node.level + 1], node.module or ""])
            else:
                base = node.module or ""
            yield base.rstrip(".")
            yield from (base.rstrip(".") + "." + alias.name for alias in node.names)


def test_business_and_workflow_do_not_depend_on_http_or_bootstrap():
    forbidden = ("fastapi", "starlette", "casepilot.api", "casepilot.main", "casepilot.bootstrap")
    violations = []
    for directory in ("analyses", "cases", "workflow", "model", "knowledge", "persistence"):
        for path in (PACKAGE / directory).rglob("*.py"):
            for module in imported_modules(path):
                if any(module == prefix or module.startswith(prefix + ".") for prefix in forbidden):
                    violations.append(f"{path.relative_to(PACKAGE)} -> {module}")
    assert not violations, "HTTP/composition imports crossed into core modules: " + repr(violations)


def test_graph_definition_does_not_call_storage_or_providers():
    for filename in ("agent_graph.py", "workspace_graph.py"):
        path = PACKAGE / "workflow" / filename
        forbidden = ("psycopg", "psycopg_pool", "httpx", "casepilot.persistence", "casepilot.model")
        assert not any(
            module == prefix or module.startswith(prefix + ".")
            for module in imported_modules(path)
            for prefix in forbidden
        ), "Graph topology must delegate effects to nodes and injected dependencies"
        assert not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"execute", "mutate", "post", "get_case", "build_report"}
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        ), "Graph construction must not execute business effects"


def test_schemas_do_not_import_runtime_services():
    for path in (PACKAGE / "schemas").rglob("*.py"):
        assert not any(
            module.startswith("casepilot.") and not module.startswith("casepilot.schemas")
            for module in imported_modules(path)
        ), "Schema export must not initialize runtime services"


def test_application_factories_have_independent_task_lifecycles(monkeypatch):
    from casepilot.main import create_app
    from fastapi.testclient import TestClient

    monkeypatch.setenv("CASEPILOT_STORAGE", "memory")
    first_app, second_app = create_app(), create_app()
    with TestClient(first_app) as first, TestClient(second_app) as second:
        response = first.post("/api/cases/CASE-2026-001/conversations", json={})
        assert response.status_code == 503
        assert first.get("/api/analyses").json() == []
        assert second.get("/api/analyses").json() == []
        assert first_app.state.store is not second_app.state.store

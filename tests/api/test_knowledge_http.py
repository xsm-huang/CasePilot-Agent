"""Real API boundary tests with credentials blank; no provider calls."""

import time
from uuid import UUID

import httpx
import psycopg
import pytest
from casepilot.schemas.knowledge import V1KnowledgeGeneration
from conftest import ApiProcess
from fastapi.testclient import TestClient
from pdf_fixtures import scanned_pdf, text_pdf


def assert_error(response, status, code):
    assert response.status_code == status, response.text
    result = response.json()
    assert result["code"] == code
    assert isinstance(result["message"], str)
    UUID(result["requestId"])
    return result


def settled_generation(client, generation_id):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        response = client.get(f"/knowledge/generations/{generation_id}")
        assert response.status_code == 200, response.text
        result = response.json()
        V1KnowledgeGeneration.model_validate(result)
        if result["status"] in ("ready", "failed"):
            return result
        time.sleep(0.03)
    raise AssertionError("Knowledge generation did not settle")


def test_memory_knowledge_is_explicitly_unavailable(api):
    assert_error(api.get("/knowledge/documents"), 503, "KNOWLEDGE_UNAVAILABLE")


@pytest.mark.parametrize(
    "exception,status,code",
    [
        (psycopg.OperationalError("private database password"), 503, "DEPENDENCY_UNAVAILABLE"),
        (RuntimeError("private application token"), 500, "INTERNAL_ERROR"),
    ],
)
def test_component_dependency_errors_are_redacted(monkeypatch, caplog, exception, status, code):
    from casepilot.main import app

    monkeypatch.setenv("CASEPILOT_STORAGE", "memory")

    class BrokenKnowledge:
        async def list_documents(self):
            raise exception

    with TestClient(app) as client:
        app.state.knowledge = BrokenKnowledge()
        response = client.get("/api/knowledge/documents")
        assert_error(response, status, code)
    assert "private" not in response.text
    assert "private" not in caplog.text


@pytest.mark.database
def test_real_multipart_boundary_parse_errors_missing_key_and_retry(postgres_env):
    server = ApiProcess(postgres_env).start()
    try:
        with httpx.Client(base_url=server.base, timeout=10) as client:
            metadata = {"productCode": "AUTO", "clauseVersion": "2025-01"}
            assert client.get("/knowledge/documents").json() == []
            assert_error(client.get("/knowledge/generations/missing"), 404, "GENERATION_NOT_FOUND")
            assert_error(
                client.post(
                    "/knowledge/documents",
                    data=metadata,
                    files={"file": ("plain.txt", b"Not PDF", "text/plain")},
                ),
                415,
                "UNSUPPORTED_DOCUMENT",
            )
            assert_error(
                client.post(
                    "/knowledge/documents",
                    data=metadata,
                    files={"file": ("empty.pdf", b"", "application/pdf")},
                ),
                422,
                "DOCUMENT_PARSE_FAILED",
            )
            assert_error(
                client.post(
                    "/knowledge/documents",
                    data=metadata,
                    files={
                        "file": (
                            "huge.pdf",
                            b"%PDF-" + b"x" * (10 * 1024 * 1024),
                            "application/pdf",
                        )
                    },
                ),
                413,
                "DOCUMENT_TOO_LARGE",
            )
            assert_error(
                client.post(
                    "/knowledge/documents",
                    files={"file": ("missing-fields.pdf", text_pdf(["Clause"]), "application/pdf")},
                ),
                400,
                "INVALID_REQUEST",
            )
            assert client.get("/knowledge/documents").json() == []

            for filename, content, reason in [
                ("corrupt.pdf", b"%PDF-1.7\nmalformed", "PDF_PARSE_FAILED"),
                (
                    "encrypted.pdf",
                    text_pdf(["Clause"], password="private-password"),
                    "ENCRYPTED_PDF",
                ),
                ("scanned.pdf", scanned_pdf(), "PDF_NO_TEXT"),
            ]:
                response = client.post(
                    "/knowledge/documents",
                    data=metadata,
                    files={"file": (filename, content, "application/pdf")},
                )
                assert response.status_code == 202, response.text
                uploaded = response.json()
                V1KnowledgeGeneration.model_validate(uploaded)
                failed = settled_generation(client, uploaded["generationId"])
                assert failed["status"] == "failed"
                assert failed["error"]["code"] == "DOCUMENT_PARSE_FAILED"
                assert failed["error"]["reasonCode"] == reason
                assert failed["embeddedCount"] == 0
                assert failed["isActive"] is False

            response = client.post(
                "/knowledge/documents",
                data=metadata,
                files={"file": ("valid.pdf", text_pdf(["Invoice clause"]), "application/pdf")},
            )
            assert response.status_code == 202, response.text
            generation_id = response.json()["generationId"]
            failed = settled_generation(client, generation_id)
            assert failed["status"] == "failed"
            assert failed["error"]["code"] == "ZHIPU_API_KEY"
            assert failed["isActive"] is False
            path = f"/knowledge/generations/{generation_id}/retry"
            assert_error(
                client.post(path, json={"expectedRevision": failed["revision"]}),
                400,
                "INVALID_REQUEST",
            )
            assert_error(
                client.post(
                    path,
                    json={"expectedRevision": failed["revision"] - 1},
                    headers={"Idempotency-Key": "stale"},
                ),
                409,
                "GENERATION_CONFLICT",
            )
            retry = client.post(
                path,
                json={"expectedRevision": failed["revision"]},
                headers={"Idempotency-Key": "retry-valid"},
            )
            assert retry.status_code == 202, retry.text
            retry_result = retry.json()
            V1KnowledgeGeneration.model_validate(retry_result)
            assert retry_result["attempt"] == 2
            same = client.post(
                path,
                json={"expectedRevision": failed["revision"]},
                headers={"Idempotency-Key": "retry-valid"},
            )
            assert same.status_code == 202
            assert same.json() == retry_result
            assert all(not row["isActive"] for row in client.get("/knowledge/documents").json())
    finally:
        server.stop()

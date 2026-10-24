"""Actual vector(1024) SQL with fake embeddings; not semantic quality evidence."""

import asyncio
import sys

import pytest
from casepilot.knowledge.config import PROFILE
from casepilot.knowledge.errors import KnowledgeOperationError
from casepilot.knowledge.repository import PostgresKnowledgeRepository
from casepilot.knowledge.service import KnowledgeService
from pdf_fixtures import text_pdf
from psycopg.errors import ForeignKeyViolation
from psycopg_pool import AsyncConnectionPool

pytestmark = pytest.mark.database


class FakeEmbedding:
    def __init__(self, fail_at=None, vector=None):
        self.calls = []
        self.fail_at = fail_at
        self.vector = vector if vector is not None else [0.25] * 1024

    async def __call__(self, texts):
        self.calls.append(texts)
        if len(self.calls) == self.fail_at:
            raise RuntimeError("private-provider-secret")
        return [self.vector.copy() for _ in texts]


def run_database(environment, scenario):
    async def run():
        async with AsyncConnectionPool(environment["DATABASE_URL"], open=False) as pool:
            await pool.wait()
            repository = PostgresKnowledgeRepository(pool, environment["CASEPILOT_DB_SCHEMA"])
            await repository.setup()
            await scenario(repository)

    if sys.platform == "win32":
        return asyncio.run(run(), loop_factory=asyncio.SelectorEventLoop)
    return asyncio.run(run())


async def publish(
    service,
    text="Article 1. Repair invoice supports actual cost.",
    product="AUTO",
    version="2025-01",
    expected=None,
):
    queued = await service.import_document(
        "self-authored.pdf", text_pdf([text]), product, version, expected
    )
    assert queued["status"] == "queued"
    assert await service.process_next() is True
    result = await service.get_generation(queued["generationId"])
    assert result["status"] == "ready", result
    assert result["isActive"] is True
    return result


def test_actual_vector_sql_and_metadata_generation_profile_isolation(postgres_env):
    async def scenario(repo):
        embedder = FakeEmbedding()
        service = KnowledgeService(repo, embedder)
        old = await publish(service)
        other_product = await publish(service, product="OTHER")
        other_version = await publish(service, version="2024-01")
        new = await publish(
            service, text="Article 2. New repair invoice evidence.", expected=old["generationId"]
        )
        assert (await repo.get_generation(old["generationId"]))["isActive"] is False
        for generation in (old, new, other_product, other_version):
            rows = await service.search(
                generation["productCode"],
                generation["clauseVersion"],
                generation["generationId"],
                "invoice",
            )
            assert rows
            assert {r["generationId"] for r in rows} == {generation["generationId"]}
            assert {r["productCode"] for r in rows} == {generation["productCode"]}
            assert {r["clauseVersion"] for r in rows} == {generation["clauseVersion"]}
            assert all(
                r["page"] == 1 and r["content"] and r["documentId"] == generation["documentId"]
                for r in rows
            )
        before = len(embedder.calls)
        for product, version, generation_id, profile in [
            ("OTHER", "2025-01", old["generationId"], PROFILE),
            ("AUTO", "2024-01", old["generationId"], PROFILE),
            ("AUTO", "2025-01", old["generationId"], "wrong-profile"),
            ("AUTO", "missing", old["generationId"], PROFILE),
        ]:
            with pytest.raises(KnowledgeOperationError) as caught:
                await service.search(product, version, generation_id, "invoice", profile=profile)
            assert caught.value.code in {"EMBEDDING_PROFILE_MISMATCH", "KNOWLEDGE_NOT_READY"}
        assert len(embedder.calls) == before, "Invalid metadata must fail before embedding"
        async with repo.pool.connection() as conn:
            cur = await conn.execute(
                repo.sql(
                    "SELECT format_type(a.atttypid,a.atttypmod) FROM pg_attribute a WHERE a.attrelid='{s}.knowledge_chunks'::regclass AND a.attname='embedding'"
                )
            )
            assert (await cur.fetchone())[0] == "vector(1024)"
            cur = await conn.execute(
                repo.sql(
                    "SELECT min(vector_dims(embedding)),max(vector_dims(embedding)) FROM {s}.knowledge_chunks"
                )
            )
            assert await cur.fetchone() == (1024, 1024)

    run_database(postgres_env, scenario)


def test_duplicate_import_reuses_generation_and_idempotency_conflict(postgres_env):
    async def scenario(repo):
        service = KnowledgeService(repo, FakeEmbedding())
        content = text_pdf(["Article 1. Original invoice clause."])
        first = await service.import_document(
            "first.pdf", content, "AUTO", "2025", idempotency_key="upload-1"
        )
        same = await service.import_document(
            "first.pdf", content, "AUTO", "2025", idempotency_key="upload-1"
        )
        assert same == first
        renamed = await service.import_document("renamed.pdf", content, "AUTO", "2025")
        assert renamed["generationId"] == first["generationId"]
        with pytest.raises(KnowledgeOperationError) as caught:
            await service.import_document(
                "first.pdf",
                text_pdf(["Different content"]),
                "AUTO",
                "2025",
                idempotency_key="upload-1",
            )
        assert caught.value.code == "IDEMPOTENCY_CONFLICT"
        assert len(await repo.list_documents()) == 1
        await service.process_next()
        reused_ready = await service.import_document("again.pdf", content, "AUTO", "2025")
        assert reused_ready["generationId"] == first["generationId"]
        assert reused_ready["status"] == "ready"

    run_database(postgres_env, scenario)


def test_same_active_pdf_with_explicit_current_generation_is_a_noop(postgres_env):
    async def scenario(repo):
        embedder = FakeEmbedding()
        service = KnowledgeService(repo, embedder)
        content = text_pdf(["Same active invoice content"])
        initial = await service.import_document("first.pdf", content, "AUTO", "2025-01")
        assert await service.process_next() is True
        active = await service.get_generation(initial["generationId"])
        assert active["isActive"] is True
        calls = len(embedder.calls)

        async def counts():
            async with repo.pool.connection() as conn:
                cur = await conn.execute(
                    repo.sql(
                        "SELECT (SELECT count(*) FROM {s}.knowledge_documents),(SELECT count(*) FROM {s}.knowledge_generations),(SELECT count(*) FROM {s}.knowledge_chunks)"
                    )
                )
                return await cur.fetchone()

        before = await counts()
        reused = await service.import_document(
            "renamed.pdf", content, "AUTO", "2025-01", active["generationId"], "repeat-current"
        )
        assert reused["generationId"] == active["generationId"]
        assert reused["documentId"] == active["documentId"]
        assert reused["status"] == "ready"
        assert reused["isActive"] is True
        assert await service.process_next() is False
        assert len(embedder.calls) == calls
        assert await counts() == before

    run_database(postgres_env, scenario)


def test_query_during_embedding_sees_only_prior_publication(postgres_env):
    async def scenario(repo):
        old = await publish(KnowledgeService(repo, FakeEmbedding()))
        entered, release = asyncio.Event(), asyncio.Event()

        async def paused_embedding(texts):
            entered.set()
            await release.wait()
            return [[0.25] * 1024 for _ in texts]

        candidate_service = KnowledgeService(repo, paused_embedding)
        queued = await candidate_service.import_document(
            "new.pdf",
            text_pdf(["New version invoice clause"]),
            "AUTO",
            "2025-01",
            old["generationId"],
        )
        task = asyncio.create_task(candidate_service.process_next())
        await asyncio.wait_for(entered.wait(), 10)
        try:
            assert await repo.active_generation("AUTO", "2025-01") == old["generationId"]
            rows = await repo.search("AUTO", "2025-01", old["generationId"], [0.25] * 1024)
            assert rows and {row["generationId"] for row in rows} == {old["generationId"]}
            with pytest.raises(KnowledgeOperationError) as caught:
                await repo.search("AUTO", "2025-01", queued["generationId"], [0.25] * 1024)
            assert caught.value.code == "KNOWLEDGE_NOT_READY"
        finally:
            release.set()
            await task
        assert await repo.active_generation("AUTO", "2025-01") == queued["generationId"]

    run_database(postgres_env, scenario)


def test_schema_migrations_are_idempotent_and_reject_unknown_version(postgres_env):
    async def scenario(repo):
        await repo.setup()
        async with repo.pool.connection() as conn:
            cur = await conn.execute(
                repo.sql("SELECT version FROM {s}.knowledge_migrations ORDER BY version")
            )
            assert await cur.fetchall() == [(1,), (2,)]
            await conn.execute(
                repo.sql("INSERT INTO {s}.knowledge_migrations(version) VALUES (999)")
            )
        with pytest.raises(RuntimeError, match="Unsupported knowledge schema migration version"):
            await repo.setup()

    run_database(postgres_env, scenario)


def test_database_rejects_cross_scope_publication_reference(postgres_env):
    async def scenario(repo):
        old = await publish(KnowledgeService(repo, FakeEmbedding()))
        with pytest.raises(ForeignKeyViolation):
            async with repo.pool.connection() as conn:
                await conn.execute(
                    repo.sql("INSERT INTO {s}.knowledge_publications VALUES (%s,%s,%s)"),
                    ("OTHER", "2025-01", old["generationId"]),
                )
        assert await repo.active_generation("AUTO", "2025-01") == old["generationId"]

    run_database(postgres_env, scenario)


def test_failed_later_embedding_batch_never_replaces_active_and_retry_retains_attempt(postgres_env):
    async def scenario(repo):
        service = KnowledgeService(repo, FakeEmbedding())
        old = await publish(service)
        failing = KnowledgeService(repo, FakeEmbedding(fail_at=2))
        content = text_pdf([f"Page {n}. New replacement invoice clause." for n in range(20)])
        queued = await failing.import_document(
            "replacement.pdf", content, "AUTO", "2025-01", old["generationId"]
        )
        await failing.process_next()
        failed = await repo.get_generation(queued["generationId"])
        assert failed["status"] == "failed"
        assert failed["embeddedCount"] == 16
        assert failed["isActive"] is False
        assert "private" not in str(failed["error"])
        assert await repo.active_generation("AUTO", "2025-01") == old["generationId"]
        assert (await service.search("AUTO", "2025-01", None, "invoice"))[0]["generationId"] == old[
            "generationId"
        ]
        with pytest.raises(KnowledgeOperationError) as caught:
            await service.retry(failed["generationId"], failed["revision"] - 1)
        assert caught.value.code == "GENERATION_CONFLICT"
        retry = await service.retry(failed["generationId"], failed["revision"], "retry-1")
        assert retry["attempt"] == 2
        assert retry["attempts"][0]["status"] == "failed"
        assert retry["attempts"][0]["finishedAt"]
        assert await service.retry(failed["generationId"], failed["revision"], "retry-1") == retry
        await service.process_next()
        ready = await repo.get_generation(failed["generationId"])
        assert ready["status"] == "ready"
        assert ready["embeddedCount"] == ready["chunkCount"] == 20
        assert ready["isActive"] is True

    run_database(postgres_env, scenario)


def test_compare_and_swap_publication_and_retry_cannot_rebase_without_confirmation(postgres_env):
    async def scenario(repo):
        service = KnowledgeService(repo, FakeEmbedding())
        old = await publish(service)
        a = await service.import_document(
            "a.pdf", text_pdf(["Candidate A"]), "AUTO", "2025-01", old["generationId"]
        )
        b = await service.import_document(
            "b.pdf", text_pdf(["Candidate B"]), "AUTO", "2025-01", old["generationId"]
        )
        # Prepare both candidates against the same publication snapshot, then
        # concurrently execute the actual PostgreSQL CAS transactions.
        for item, text in [(a, "Candidate A"), (b, "Candidate B")]:
            await repo.update(item["generationId"], status="embedding", pageCount=1, chunkCount=1)
            await repo.add_chunks(
                item["generationId"], [{"page": 1, "ordinal": 0, "content": text}], [[0.25] * 1024]
            )
        outcomes = await asyncio.gather(
            repo.publish(a["generationId"]), repo.publish(b["generationId"]), return_exceptions=True
        )
        assert sum(outcome is None for outcome in outcomes) == 1
        assert (
            sum(
                isinstance(outcome, KnowledgeOperationError)
                and outcome.code == "GENERATION_CONFLICT"
                for outcome in outcomes
            )
            == 1
        )
        winner = await repo.active_generation("AUTO", "2025-01")
        loser_id = next(item["generationId"] for item in (a, b) if item["generationId"] != winner)
        await repo.update(
            loser_id, status="failed", error={"code": "PUBLICATION_CONFLICT", "message": "Conflict"}
        )
        loser = await repo.get_generation(loser_id)
        with pytest.raises(KnowledgeOperationError) as caught:
            await service.retry(loser_id, loser["revision"])
        assert caught.value.code == "GENERATION_CONFLICT"
        assert await repo.active_generation("AUTO", "2025-01") == winner
        assert (await repo.get_generation(loser_id))["attempt"] == 1

    run_database(postgres_env, scenario)


@pytest.mark.parametrize(
    "vector",
    [[0.25], [0] * 1024, [True] * 1024, [float("nan")] * 1024, [1e40] * 1024, [1e-50] * 1024],
)
def test_invalid_embedding_never_publishes(postgres_env, vector):
    async def scenario(repo):
        service = KnowledgeService(repo, FakeEmbedding(vector=vector))
        queued = await service.import_document(
            "invalid-vector.pdf", text_pdf(["Invoice clause"]), "AUTO", "2025"
        )
        await service.process_next()
        failed = await repo.get_generation(queued["generationId"])
        assert failed["status"] == "failed"
        assert failed["embeddedCount"] == 0
        assert failed["isActive"] is False
        async with repo.pool.connection() as conn:
            cur = await conn.execute(repo.sql("SELECT count(*) FROM {s}.knowledge_publications"))
            assert (await cur.fetchone())[0] == 0

    run_database(postgres_env, scenario)

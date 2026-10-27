"""PostgreSQL persistence. Publication is a compare-and-swap transaction."""

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from psycopg.types.json import Jsonb

from ..model.embeddings import validate_embedding
from ..persistence.identifiers import identifier
from ..persistence.knowledge_migrations import migrate_knowledge
from .config import PROCESSING, PROFILE
from .errors import KnowledgeOperationError


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class PostgresKnowledgeRepository:
    def __init__(self, pool, schema="casepilot_python"):
        self.pool = pool
        self.schema = identifier(schema)

    def sql(self, query):
        # schema is validated above, all business values remain bound parameters.
        return query.replace("{s}", f'"{self.schema}"')

    async def setup(self):
        await migrate_knowledge(self.pool, self.schema)

    @staticmethod
    def public(snapshot, active):
        return {k: deepcopy(v) for k, v in snapshot.items() if not k.startswith("_")} | {
            "isActive": active
        }

    async def _active(self, conn, product, version):
        cur = await conn.execute(
            self.sql(
                "SELECT generation_id FROM {s}.knowledge_publications WHERE product_code=%s AND clause_version=%s"
            ),
            (product, version),
        )
        row = await cur.fetchone()
        return row[0] if row else None

    async def _guard(self, conn, product, version):
        await conn.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (f"knowledge:{self.schema}:{product}:{version}",),
        )

    async def _request(self, conn, scope, key, fingerprint):
        if not key:
            return None
        cur = await conn.execute(
            self.sql(
                "SELECT fingerprint,response FROM {s}.knowledge_requests WHERE scope=%s AND key=%s"
            ),
            (scope, key),
        )
        row = await cur.fetchone()
        if row and row[0] != fingerprint:
            raise KnowledgeOperationError(
                "IDEMPOTENCY_CONFLICT", "同一 Idempotency-Key 不能用于不同请求。"
            )
        return row[1] if row else None

    async def _record(self, conn, scope, key, fingerprint, response):
        if key:
            await conn.execute(
                self.sql("INSERT INTO {s}.knowledge_requests VALUES (%s,%s,%s,%s)"),
                (scope, key, fingerprint, Jsonb(response)),
            )

    async def import_document(
        self,
        file_name,
        content,
        product_code,
        clause_version,
        expected_generation_id=None,
        idempotency_key=None,
    ):
        sha = hashlib.sha256(content).hexdigest()
        # The expected publication is part of an import's intent. Confirming a newer
        # publication creates a new generation; retries never silently retarget an old one.
        fingerprint = hashlib.sha256(
            json.dumps(
                [sha, product_code, clause_version, PROCESSING, expected_generation_id],
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
        request_fingerprint = hashlib.sha256(
            json.dumps(
                [fingerprint, file_name, expected_generation_id], ensure_ascii=False
            ).encode()
        ).hexdigest()
        async with self.pool.connection() as conn:
            async with conn.transaction():
                await self._guard(conn, product_code, clause_version)
                # Lock idempotency independently of metadata to serialize same-key mismatches.
                if idempotency_key:
                    await conn.execute(
                        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                        (f"knowledge-request:{self.schema}:import:{idempotency_key}",),
                    )
                reused = await self._request(conn, "import", idempotency_key, request_fingerprint)
                if reused:
                    return reused
                active = await self._active(conn, product_code, clause_version)
                cur = await conn.execute(
                    self.sql("SELECT snapshot FROM {s}.knowledge_generations WHERE fingerprint=%s"),
                    (fingerprint,),
                )
                row = await cur.fetchone()
                if row:
                    result = self.public(row[0], active == row[0]["generationId"])
                    await self._record(conn, "import", idempotency_key, request_fingerprint, result)
                    return result
                if active != expected_generation_id:
                    raise KnowledgeOperationError(
                        "GENERATION_CONFLICT", "生效知识版本已变化，请刷新后确认替换。"
                    )
                if active:
                    # Confirming the already-active file is a no-op. Only a known
                    # identical processing/profile can be reused; inactive generations
                    # are never republished by this shortcut.
                    cur = await conn.execute(
                        self.sql(
                            "SELECT g.snapshot FROM {s}.knowledge_generations g "
                            "JOIN {s}.knowledge_documents d ON d.id=g.document_id "
                            "WHERE g.id=%s AND g.product_code=%s AND g.clause_version=%s "
                            "AND g.profile=%s AND d.sha256=%s "
                            "AND g.snapshot->>'_processing'=%s "
                            "AND g.snapshot->>'status'='ready'"
                        ),
                        (active, product_code, clause_version, PROFILE, sha, PROCESSING),
                    )
                    active_row = await cur.fetchone()
                    if active_row:
                        result = self.public(active_row[0], True)
                        await self._record(
                            conn, "import", idempotency_key, request_fingerprint, result
                        )
                        return result
                generation_id, document_id, timestamp = str(uuid4()), str(uuid4()), now()
                snapshot = {
                    "generationId": generation_id,
                    "documentId": document_id,
                    "productCode": product_code,
                    "clauseVersion": clause_version,
                    "fileName": file_name,
                    "sha256": sha,
                    "status": "queued",
                    "revision": 1,
                    "attempt": 1,
                    "pageCount": 0,
                    "chunkCount": 0,
                    "embeddedCount": 0,
                    "error": None,
                    "createdAt": timestamp,
                    "updatedAt": timestamp,
                    "attempts": [
                        {
                            "attempt": 1,
                            "status": "queued",
                            "startedAt": timestamp,
                            "finishedAt": None,
                            "error": None,
                        }
                    ],
                    "_expectedGenerationId": active,
                    "_processing": PROCESSING,
                }
                await conn.execute(
                    self.sql("INSERT INTO {s}.knowledge_documents VALUES (%s,%s,%s,%s)"),
                    (document_id, file_name, sha, content),
                )
                await conn.execute(
                    self.sql("INSERT INTO {s}.knowledge_generations VALUES (%s,%s,%s,%s,%s,%s,%s)"),
                    (
                        generation_id,
                        document_id,
                        fingerprint,
                        product_code,
                        clause_version,
                        PROFILE,
                        Jsonb(snapshot),
                    ),
                )
                result = self.public(snapshot, False)
                await self._record(conn, "import", idempotency_key, request_fingerprint, result)
                return result

    async def get_generation(self, generation_id):
        async with self.pool.connection() as conn:
            cur = await conn.execute(
                self.sql(
                    "SELECT g.snapshot, p.generation_id=g.id FROM {s}.knowledge_generations g LEFT JOIN {s}.knowledge_publications p ON p.product_code=g.product_code AND p.clause_version=g.clause_version WHERE g.id=%s"
                ),
                (generation_id,),
            )
            row = await cur.fetchone()
            if not row:
                raise KnowledgeOperationError("GENERATION_NOT_FOUND", "知识索引不存在。")
            return self.public(row[0], bool(row[1]))

    async def list_documents(self):
        async with self.pool.connection() as conn:
            cur = await conn.execute(
                self.sql(
                    "SELECT g.snapshot, p.generation_id=g.id FROM {s}.knowledge_generations g LEFT JOIN {s}.knowledge_publications p ON p.product_code=g.product_code AND p.clause_version=g.clause_version ORDER BY g.snapshot->>'createdAt' DESC"
                )
            )
            return [self.public(row[0], bool(row[1])) for row in await cur.fetchall()]

    async def _snapshot(self, conn, generation_id):
        cur = await conn.execute(
            self.sql("SELECT snapshot FROM {s}.knowledge_generations WHERE id=%s FOR UPDATE"),
            (generation_id,),
        )
        row = await cur.fetchone()
        if not row:
            raise KnowledgeOperationError("GENERATION_NOT_FOUND", "知识索引不存在。")
        return row[0]

    async def _save(self, conn, snapshot):
        snapshot["revision"] += 1
        snapshot["updatedAt"] = now()
        attempt = snapshot["attempts"][-1]
        attempt["status"] = snapshot["status"]
        if snapshot["status"] in ("failed", "ready"):
            attempt.update(finishedAt=now(), error=snapshot["error"])
        await conn.execute(
            self.sql("UPDATE {s}.knowledge_generations SET snapshot=%s WHERE id=%s"),
            (Jsonb(snapshot), snapshot["generationId"]),
        )

    async def update(self, generation_id, **patch):
        async with self.pool.connection() as conn:
            async with conn.transaction():
                snapshot = await self._snapshot(conn, generation_id)
                snapshot.update(patch)
                await self._save(conn, snapshot)

    async def next_queued(self):
        async with self.pool.connection() as conn:
            cur = await conn.execute(
                self.sql(
                    "SELECT g.id,d.content FROM {s}.knowledge_generations g JOIN {s}.knowledge_documents d ON d.id=g.document_id WHERE g.snapshot->>'status'='queued' ORDER BY g.snapshot->>'createdAt' LIMIT 1"
                )
            )
            return await cur.fetchone()

    async def reconcile(self):
        for generation in await self.list_documents():
            if (
                generation["status"] in ("parsing", "chunking", "embedding")
                and not generation["isActive"]
            ):
                await self.update(
                    generation["generationId"],
                    status="failed",
                    error={
                        "code": "INDEXING_INTERRUPTED",
                        "message": "索引任务被进程中断，请显式重试。",
                    },
                )

    async def retry(self, generation_id, expected_revision, idempotency_key=None):
        fingerprint = str(expected_revision)
        scope = f"retry:{generation_id}"
        async with self.pool.connection() as conn:
            async with conn.transaction():
                snapshot = await self._snapshot(conn, generation_id)
                reused = await self._request(conn, scope, idempotency_key, fingerprint)
                if reused:
                    return reused
                await self._guard(conn, snapshot["productCode"], snapshot["clauseVersion"])
                active = await self._active(
                    conn, snapshot["productCode"], snapshot["clauseVersion"]
                )
                if (
                    snapshot["revision"] != expected_revision
                    or snapshot["status"] != "failed"
                    or active == generation_id
                ):
                    raise KnowledgeOperationError(
                        "GENERATION_CONFLICT", "仅允许重试版本匹配的失败且未生效索引。"
                    )
                if active != snapshot["_expectedGenerationId"]:
                    raise KnowledgeOperationError(
                        "GENERATION_CONFLICT", "生效版本已变化，请重新上传并明确确认替换版本。"
                    )
                await conn.execute(
                    self.sql("DELETE FROM {s}.knowledge_chunks WHERE generation_id=%s"),
                    (generation_id,),
                )
                snapshot.update(
                    status="queued",
                    error=None,
                    pageCount=0,
                    chunkCount=0,
                    embeddedCount=0,
                    attempt=snapshot["attempt"] + 1,
                )
                snapshot["attempts"].append(
                    {
                        "attempt": snapshot["attempt"],
                        "status": "queued",
                        "startedAt": now(),
                        "finishedAt": None,
                        "error": None,
                    }
                )
                await self._save(conn, snapshot)
                result = self.public(snapshot, False)
                await self._record(conn, scope, idempotency_key, fingerprint, result)
                return result

    async def add_chunks(self, generation_id, chunks, vectors):
        async with self.pool.connection() as conn:
            async with conn.transaction():
                for chunk, vector in zip(chunks, vectors, strict=True):
                    await conn.execute(
                        self.sql(
                            "INSERT INTO {s}.knowledge_chunks VALUES (%s,%s,%s,%s,%s,%s::vector)"
                        ),
                        (
                            str(uuid4()),
                            generation_id,
                            chunk["page"],
                            chunk["ordinal"],
                            chunk["content"],
                            str(vector),
                        ),
                    )
                snapshot = await self._snapshot(conn, generation_id)
                snapshot["embeddedCount"] += len(chunks)
                await self._save(conn, snapshot)

    async def publish(self, generation_id):
        async with self.pool.connection() as conn:
            async with conn.transaction():
                snapshot = await self._snapshot(conn, generation_id)
                await self._guard(conn, snapshot["productCode"], snapshot["clauseVersion"])
                active = await self._active(
                    conn, snapshot["productCode"], snapshot["clauseVersion"]
                )
                cur = await conn.execute(
                    self.sql("SELECT count(*) FROM {s}.knowledge_chunks WHERE generation_id=%s"),
                    (generation_id,),
                )
                count = (await cur.fetchone())[0]
                if (
                    snapshot["status"] != "embedding"
                    or not count
                    or count != snapshot["chunkCount"]
                    or count != snapshot["embeddedCount"]
                ):
                    raise KnowledgeOperationError("GENERATION_CONFLICT", "索引不完整，不能发布。")
                if active != snapshot["_expectedGenerationId"]:
                    raise KnowledgeOperationError(
                        "GENERATION_CONFLICT", "发布指针已变化，请显式重试。"
                    )
                await conn.execute(
                    self.sql(
                        "INSERT INTO {s}.knowledge_publications VALUES (%s,%s,%s) ON CONFLICT(product_code,clause_version) DO UPDATE SET generation_id=EXCLUDED.generation_id"
                    ),
                    (snapshot["productCode"], snapshot["clauseVersion"], generation_id),
                )
                snapshot.update(status="ready", error=None)
                await self._save(conn, snapshot)

    async def search(
        self, product_code, clause_version, generation_id, vector, limit=4, profile=PROFILE
    ):
        if profile != PROFILE:
            raise KnowledgeOperationError("EMBEDDING_PROFILE_MISMATCH", "向量配置不匹配。")
        if type(limit) is not int or not 1 <= limit <= 12:
            raise KnowledgeOperationError("INVALID_REQUEST", "检索条数必须介于 1 与 12。")
        vector = validate_embedding(vector)
        async with self.pool.connection() as conn:
            cur = await conn.execute(
                self.sql(
                    "SELECT id FROM {s}.knowledge_generations WHERE id=%s AND product_code=%s AND clause_version=%s AND profile=%s AND snapshot->>'status'='ready'"
                ),
                (generation_id, product_code, clause_version, profile),
            )
            if not await cur.fetchone():
                raise KnowledgeOperationError(
                    "KNOWLEDGE_NOT_READY", "没有匹配险种、版本和向量配置的可用索引。"
                )
            cur = await conn.execute(
                self.sql(
                    "SELECT c.id,c.page,c.content,c.ordinal,c.embedding <=> %s::vector AS distance,g.document_id,d.file_name FROM {s}.knowledge_chunks c JOIN {s}.knowledge_generations g ON g.id=c.generation_id JOIN {s}.knowledge_documents d ON d.id=g.document_id WHERE c.generation_id=%s AND g.product_code=%s AND g.clause_version=%s AND g.profile=%s ORDER BY distance,c.ordinal LIMIT %s"
                ),
                (str(vector), generation_id, product_code, clause_version, profile, limit),
            )
            return [
                {
                    "chunkId": row[0],
                    "page": row[1],
                    "content": row[2],
                    "ordinal": row[3],
                    "distance": row[4],
                    "documentId": row[5],
                    "fileName": row[6],
                    "generationId": generation_id,
                    "productCode": product_code,
                    "clauseVersion": clause_version,
                }
                for row in await cur.fetchall()
            ]

    async def citation_context(self, citation):
        """Read bounded neighbours from the exact immutable source of a task citation."""
        async with self.pool.connection() as conn:
            cursor = await conn.execute(
                self.sql(
                    "SELECT c.ordinal FROM {s}.knowledge_chunks c JOIN {s}.knowledge_generations g ON g.id=c.generation_id "
                    "WHERE c.id=%s AND g.id=%s AND g.document_id=%s AND g.product_code=%s AND g.clause_version=%s AND g.profile=%s AND g.snapshot->>'status'='ready'"
                ),
                (
                    citation["chunkId"],
                    citation["generationId"],
                    citation["documentId"],
                    citation["productCode"],
                    citation["clauseVersion"],
                    PROFILE,
                ),
            )
            center = await cursor.fetchone()
            if not center:
                raise KnowledgeOperationError("GENERATION_NOT_FOUND", "引用来源不可用。")
            result = {}
            for name, operator, order in (("previous", "<", "DESC"), ("next", ">", "ASC")):
                cursor = await conn.execute(
                    self.sql(
                        "SELECT id,page,ordinal,content FROM {s}.knowledge_chunks WHERE generation_id=%s AND ordinal "
                        + operator
                        + " %s ORDER BY ordinal "
                        + order
                        + " LIMIT 1"
                    ),
                    (citation["generationId"], center[0]),
                )
                row = await cursor.fetchone()
                result[name] = (
                    dict(zip(("chunkId", "page", "ordinal", "content"), row, strict=True))
                    if row
                    else None
                )
            return {"citation": citation, **result}

    async def generation_profile(self, generation_id):
        async with self.pool.connection() as conn:
            cursor = await conn.execute(
                self.sql("SELECT profile FROM {s}.knowledge_generations WHERE id=%s"),
                (generation_id,),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def active_generation(self, product_code, clause_version):
        async with self.pool.connection() as conn:
            generation_id = await self._active(conn, product_code, clause_version)
        if not generation_id:
            raise KnowledgeOperationError(
                "KNOWLEDGE_NOT_READY", "该险种与业务版本没有生效知识索引。"
            )
        return generation_id

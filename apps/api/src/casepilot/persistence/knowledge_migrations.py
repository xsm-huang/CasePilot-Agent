"""Versioned knowledge schema migrations with the existing transaction lock."""


async def migrate_knowledge(pool, schema):
    def render(query):
        return query.replace("{s}", f'"{schema}"')

    migrations = {
        1: [
            "CREATE TABLE {s}.knowledge_documents(id text PRIMARY KEY, file_name text NOT NULL, sha256 text NOT NULL, content bytea NOT NULL CHECK(octet_length(content) <= 10485760))",
            "CREATE TABLE {s}.knowledge_generations(id text PRIMARY KEY, document_id text NOT NULL REFERENCES {s}.knowledge_documents(id), fingerprint text NOT NULL UNIQUE, product_code text NOT NULL, clause_version text NOT NULL, profile text NOT NULL, snapshot jsonb NOT NULL CHECK(snapshot->>'status' IN ('queued','parsing','chunking','embedding','ready','failed')))",
            "CREATE TABLE {s}.knowledge_publications(product_code text NOT NULL, clause_version text NOT NULL, generation_id text NOT NULL REFERENCES {s}.knowledge_generations(id), PRIMARY KEY(product_code,clause_version))",
            "CREATE TABLE {s}.knowledge_chunks(id text PRIMARY KEY, generation_id text NOT NULL REFERENCES {s}.knowledge_generations(id), page integer NOT NULL CHECK(page>0), ordinal integer NOT NULL CHECK(ordinal>=0), content text NOT NULL, embedding vector(1024) NOT NULL, UNIQUE(generation_id,ordinal))",
            "CREATE TABLE {s}.knowledge_requests(scope text NOT NULL, key text NOT NULL, fingerprint text NOT NULL, response jsonb NOT NULL, PRIMARY KEY(scope,key))",
        ],
        2: [
            "ALTER TABLE {s}.knowledge_generations ADD CONSTRAINT knowledge_generation_scope UNIQUE(product_code,clause_version,id)",
            "ALTER TABLE {s}.knowledge_publications ADD CONSTRAINT knowledge_publication_scope FOREIGN KEY(product_code,clause_version,generation_id) REFERENCES {s}.knowledge_generations(product_code,clause_version,id)",
        ],
    }
    async with pool.connection() as conn:
        async with conn.transaction():
            await conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"knowledge-migrate:{schema}",),
            )
            await conn.execute(render("CREATE SCHEMA IF NOT EXISTS {s}"))
            cur = await conn.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')"
            )
            if not (await cur.fetchone())[0]:
                raise RuntimeError("Knowledge ingestion requires the pgvector extension")
            await conn.execute(
                render(
                    "CREATE TABLE IF NOT EXISTS {s}.knowledge_migrations(version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
                )
            )
            cur = await conn.execute(
                render("SELECT version FROM {s}.knowledge_migrations ORDER BY version")
            )
            applied = {row[0] for row in await cur.fetchall()}
            if applied - migrations.keys() or (2 in applied and 1 not in applied):
                raise RuntimeError("Unsupported knowledge schema migration version")
            for version, statements in migrations.items():
                if version not in applied:
                    for statement in statements:
                        await conn.execute(render(statement))
                    await conn.execute(
                        render("INSERT INTO {s}.knowledge_migrations(version) VALUES (%s)"),
                        (version,),
                    )

"""Read-only database readiness, without provider calls or migrations."""


async def database_readiness(pool):
    result = {"configured": pool is not None, "available": False, "pgvector": False}
    if pool:
        try:
            async with pool.connection() as conn:
                cursor = await conn.execute(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')"
                )
                result.update(available=True, pgvector=(await cursor.fetchone())[0])
        except Exception:
            pass
    return result

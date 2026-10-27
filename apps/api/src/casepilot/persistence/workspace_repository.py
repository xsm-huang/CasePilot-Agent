"""Additive V1 persistence; task, event, command and message commits stay atomic."""

from psycopg.types.json import Jsonb

from ..analyses.errors import AnalysisError
from .analysis_repository import PostgresAnalysisRepository
from .identifiers import identifier


class WorkspaceRepository(PostgresAnalysisRepository):
    def __init__(self, pool, schema):
        super().__init__(pool, identifier(schema))

    def sql(self, statement):
        return statement.replace("{s}", f'"{self.schema}"')

    async def load(self):
        tasks, commands = await super().load()
        await self.migrate()
        return tasks, commands

    async def migrate(self):
        statements = [
            "CREATE TABLE {s}.conversations(id text PRIMARY KEY, case_id text NOT NULL, snapshot jsonb NOT NULL)",
            "CREATE TABLE {s}.analysis_metadata(task_id text PRIMARY KEY REFERENCES {s}.tasks(id), conversation_id text NOT NULL REFERENCES {s}.conversations(id), status text NOT NULL CHECK(status IN ('queued','running','waiting_review','resuming','recoverable','completed','rejected','failed')), revision bigint NOT NULL CHECK(revision>=0), last_seq bigint NOT NULL CHECK(last_seq>=0), UNIQUE(task_id,conversation_id))",
            "CREATE UNIQUE INDEX workspace_one_active_analysis ON {s}.analysis_metadata(conversation_id) WHERE status IN ('queued','running','waiting_review','resuming','recoverable')",
            "CREATE TABLE {s}.messages(id text PRIMARY KEY, conversation_id text NOT NULL REFERENCES {s}.conversations(id), analysis_id text NOT NULL REFERENCES {s}.tasks(id), role text NOT NULL CHECK(role IN ('user','assistant')), created_at timestamptz NOT NULL, data jsonb NOT NULL, UNIQUE(analysis_id,role), FOREIGN KEY(analysis_id,conversation_id) REFERENCES {s}.analysis_metadata(task_id,conversation_id))",
            "CREATE TABLE {s}.analysis_events(task_id text NOT NULL REFERENCES {s}.tasks(id), seq bigint NOT NULL CHECK(seq>0), event jsonb NOT NULL, PRIMARY KEY(task_id,seq))",
            "CREATE TABLE {s}.analysis_requests(scope text NOT NULL, key text NOT NULL, fingerprint text NOT NULL, response jsonb NOT NULL, PRIMARY KEY(scope,key))",
            "CREATE TABLE {s}.analysis_reviews(task_id text PRIMARY KEY REFERENCES {s}.tasks(id), interrupt_key text NOT NULL UNIQUE, decision text NOT NULL CHECK(decision IN ('approve','reject')), data jsonb NOT NULL)",
        ]
        async with self.pool.connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                    (f"workspace-migrate:{self.schema}",),
                )
                await conn.execute(
                    self.sql(
                        "CREATE TABLE IF NOT EXISTS {s}.workspace_migrations(version integer PRIMARY KEY)"
                    )
                )
                cursor = await conn.execute(
                    self.sql("SELECT version FROM {s}.workspace_migrations")
                )
                versions = {row[0] for row in await cursor.fetchall()}
                if versions - {1}:
                    raise RuntimeError("Unsupported workspace schema version")
                if 1 not in versions:
                    for statement in statements:
                        await conn.execute(self.sql(statement))
                    await conn.execute(self.sql("INSERT INTO {s}.workspace_migrations VALUES (1)"))

    async def conversations(self):
        async with self.pool.connection() as conn:
            cursor = await conn.execute(self.sql("SELECT id,snapshot FROM {s}.conversations"))
            return dict(await cursor.fetchall())

    async def _conversation(self, conn, conversation):
        await conn.execute(
            self.sql(
                "INSERT INTO {s}.conversations VALUES (%s,%s,%s) ON CONFLICT(id) DO UPDATE SET snapshot=EXCLUDED.snapshot"
            ),
            (conversation["id"], conversation["caseId"], Jsonb(conversation)),
        )

    async def save_conversation(self, conversation):
        async with self.pool.connection() as conn:
            await self._conversation(conn, conversation)

    async def request(self, scope, key, fingerprint):
        async with self.pool.connection() as conn:
            cursor = await conn.execute(
                self.sql(
                    "SELECT fingerprint,response FROM {s}.analysis_requests WHERE scope=%s AND key=%s"
                ),
                (scope, key),
            )
            row = await cursor.fetchone()
        if row and row[0] != fingerprint:
            raise AnalysisError("IDEMPOTENCY_CONFLICT", "同一幂等键不能用于不同请求。")
        return row[1] if row else None

    async def _persist(self, conn, task):
        cursor = await conn.execute(
            self.sql(
                "SELECT revision,last_seq FROM {s}.analysis_metadata WHERE task_id=%s FOR UPDATE"
            ),
            (task["id"],),
        )
        previous = await cursor.fetchone()
        previous_seq = previous[1] if previous else 0
        if previous and (previous[0] > task["revision"] or previous_seq > task["lastEventSeq"]):
            raise AnalysisError("RECOVERY_CONFLICT", "任务版本或事件游标无法安全对账。")
        events = task["events"]
        if len(events) != task["lastEventSeq"] or any(
            e["seq"] != i + 1 for i, e in enumerate(events)
        ):
            raise AnalysisError("RECOVERY_CONFLICT", "任务事件序号不连续。")
        await self._save(task, conn)
        await conn.execute(
            self.sql(
                "INSERT INTO {s}.analysis_metadata VALUES (%s,%s,%s,%s,%s) ON CONFLICT(task_id) DO UPDATE SET status=EXCLUDED.status,revision=EXCLUDED.revision,last_seq=EXCLUDED.last_seq"
            ),
            (
                task["id"],
                task["conversationId"],
                task["status"],
                task["revision"],
                task["lastEventSeq"],
            ),
        )
        for event in events[previous_seq:]:
            await conn.execute(
                self.sql("INSERT INTO {s}.analysis_events VALUES (%s,%s,%s)"),
                (task["id"], event["seq"], Jsonb(event)),
            )

    async def save(self, task):
        if task.get("schemaVersion") != 1:
            return await super().save(task)
        async with self.pool.connection() as conn:
            async with conn.transaction():
                await self._persist(conn, task)

    async def commit(
        self, task, *, command=None, request=None, message=None, conversation=None, review=None
    ):
        async with self.pool.connection() as conn:
            async with conn.transaction():
                if conversation:
                    await self._conversation(conn, conversation)
                await self._persist(conn, task)
                if command:
                    await self._insert_command(conn, command)
                if request:
                    await conn.execute(
                        self.sql("INSERT INTO {s}.analysis_requests VALUES (%s,%s,%s,%s)"),
                        (*request[:3], Jsonb(request[3])),
                    )
                if message:
                    await conn.execute(
                        self.sql("INSERT INTO {s}.messages VALUES (%s,%s,%s,%s,%s,%s)"),
                        (
                            message["id"],
                            task["conversationId"],
                            task["id"],
                            message["role"],
                            message["createdAt"],
                            Jsonb(message),
                        ),
                    )
                if review:
                    await conn.execute(
                        self.sql("INSERT INTO {s}.analysis_reviews VALUES (%s,%s,%s,%s)"),
                        (task["id"], review["interruptKey"], review["decision"], Jsonb(review)),
                    )

    async def messages(self, conversation_id, *, before=None, completed_only=False):
        async with self.pool.connection() as conn:
            if completed_only:
                # Select complete turns first: tied timestamps must not split a
                # user/assistant pair at the six-turn context boundary.
                cursor = await conn.execute(
                    self.sql(
                        "WITH recent AS (SELECT m.analysis_id,m.created_at FROM {s}.messages m "
                        "JOIN {s}.analysis_metadata a ON a.task_id=m.analysis_id "
                        "WHERE m.conversation_id=%s AND m.role='assistant' AND a.status='completed' "
                        "ORDER BY m.created_at DESC,m.analysis_id DESC LIMIT 6) "
                        "SELECT m.data FROM recent r JOIN {s}.messages m ON m.analysis_id=r.analysis_id "
                        "ORDER BY r.created_at DESC,r.analysis_id DESC,CASE m.role WHEN 'assistant' THEN 0 ELSE 1 END"
                    ),
                    (conversation_id,),
                )
                return [row[0] for row in await cursor.fetchall()]
            cutoff = ""
            parameters = [conversation_id]
            if before:
                cursor = await conn.execute(
                    self.sql(
                        "SELECT created_at,id FROM {s}.messages WHERE id=%s AND conversation_id=%s"
                    ),
                    (before, conversation_id),
                )
                row = await cursor.fetchone()
                if not row:
                    raise AnalysisError("INVALID_INPUT", "无效的消息分页位置。")
                cutoff = " AND (m.created_at,m.id)<(%s,%s)"
                parameters.extend(row)
            limit = 51
            cursor = await conn.execute(
                self.sql(
                    "SELECT m.data FROM {s}.messages m JOIN {s}.analysis_metadata a ON a.task_id=m.analysis_id WHERE m.conversation_id=%s"
                    + cutoff
                    + " ORDER BY m.created_at DESC,m.id DESC LIMIT %s"
                ),
                (*parameters, limit),
            )
            return [row[0] for row in await cursor.fetchall()]

    async def events_after(self, task_id, cursor):
        async with self.pool.connection() as conn:
            result = await conn.execute(
                self.sql(
                    "SELECT event FROM {s}.analysis_events WHERE task_id=%s AND seq>%s ORDER BY seq LIMIT 100"
                ),
                (task_id, cursor),
            )
            return [row[0] for row in await result.fetchall()]

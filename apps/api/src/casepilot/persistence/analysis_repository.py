"""PostgreSQL task/command transactions; independent from graph checkpoints."""

from psycopg import sql
from psycopg.types.json import Jsonb


class PostgresAnalysisRepository:
    def __init__(self, pool, schema):
        self.pool = pool
        self.schema = schema

    async def load(self):
        async with self.pool.connection() as conn:
            await conn.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(self.schema))
            )
            await conn.execute(
                sql.SQL(
                    "CREATE TABLE IF NOT EXISTS {}.tasks (id text PRIMARY KEY, snapshot jsonb NOT NULL)"
                ).format(sql.Identifier(self.schema))
            )
            await conn.execute(
                sql.SQL(
                    "CREATE TABLE IF NOT EXISTS {}.commands (id text PRIMARY KEY, task_id text NOT NULL, payload jsonb NOT NULL, status text NOT NULL DEFAULT 'pending', error text)"
                ).format(sql.Identifier(self.schema))
            )
            cur = await conn.execute(
                sql.SQL("SELECT id,snapshot FROM {}.tasks").format(sql.Identifier(self.schema))
            )
            tasks = {row[0]: row[1] for row in await cur.fetchall()}
            cur = await conn.execute(
                sql.SQL(
                    "SELECT id,task_id,payload,status FROM {}.commands WHERE status != 'done'"
                ).format(sql.Identifier(self.schema))
            )
            commands = {
                row[0]: {"id": row[0], "taskId": row[1], **row[2], "status": row[3]}
                for row in await cur.fetchall()
            }
        return tasks, commands

    async def _save(self, task, conn):
        if conn:
            await conn.execute(
                sql.SQL(
                    "INSERT INTO {}.tasks VALUES (%s,%s) ON CONFLICT(id) DO UPDATE SET snapshot=EXCLUDED.snapshot"
                ).format(sql.Identifier(self.schema)),
                (task["id"], Jsonb(task)),
            )

    async def save(self, task):
        async with self.pool.connection() as conn:
            await self._save(task, conn)

    async def _insert_command(self, conn, command):
        payload = {key: command[key] for key in ("kind", "review") if key in command}
        await conn.execute(
            sql.SQL("INSERT INTO {}.commands(id,task_id,payload) VALUES (%s,%s,%s)").format(
                sql.Identifier(self.schema)
            ),
            (command["id"], command["taskId"], Jsonb(payload)),
        )

    async def save_with_command(self, task, command):
        async with self.pool.connection() as conn:
            async with conn.transaction():
                await self._save(task, conn)
                await self._insert_command(conn, command)

    async def enqueue(self, command):
        async with self.pool.connection() as conn:
            await self._insert_command(conn, command)

    async def finish_command(self, command_id, error):
        async with self.pool.connection() as conn:
            await conn.execute(
                sql.SQL("UPDATE {}.commands SET status='done', error=%s WHERE id=%s").format(
                    sql.Identifier(self.schema)
                ),
                (error, command_id),
            )

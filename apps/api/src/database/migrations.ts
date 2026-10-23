import type pg from 'pg';

const migrations = [
  { version: 1, name: 'enable_pgvector', sql: 'CREATE EXTENSION IF NOT EXISTS vector' }
] as const;

/** Application migrations and official checkpoint migrations have separate ownership. */
export async function migrateDatabase(pool: pg.Pool): Promise<number> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query("SELECT pg_advisory_xact_lock(hashtext('casepilot_schema_migrations'))");
    await client.query(`CREATE TABLE IF NOT EXISTS casepilot_schema_migrations (
      version integer PRIMARY KEY,
      name text NOT NULL,
      applied_at timestamptz NOT NULL DEFAULT now()
    )`);
    const applied = await client.query<{ version: number; name: string }>(
      'SELECT version, name FROM casepilot_schema_migrations ORDER BY version'
    );
    for (const row of applied.rows) {
      if (!migrations.some(migration => migration.version === row.version && migration.name === row.name)) {
        throw new Error('DATABASE_MIGRATION_VERSION_MISMATCH');
      }
    }
    const versions = new Set(applied.rows.map(row => row.version));
    for (const migration of migrations) {
      if (versions.has(migration.version)) continue;
      await client.query(migration.sql);
      await client.query('INSERT INTO casepilot_schema_migrations (version, name) VALUES ($1, $2)',
        [migration.version, migration.name]);
    }
    await client.query('COMMIT');
    return migrations.at(-1)!.version;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

import pg from 'pg';

export function createDatabasePool(connectionString: string): pg.Pool {
  return new pg.Pool({
    connectionString,
    max: 5,
    connectionTimeoutMillis: 5000,
    idleTimeoutMillis: 10000,
    statement_timeout: 30000,
    application_name: 'casepilot-api'
  });
}

export function readDatabaseUrl(env: NodeJS.ProcessEnv = process.env): string {
  const value = env.DATABASE_URL;
  try {
    if (!value) throw new Error();
    const url = new URL(value);
    if (!['postgresql:', 'postgres:'].includes(url.protocol) || !url.hostname || !url.pathname.slice(1)) {
      throw new Error();
    }
    return value;
  } catch {
    // Never place the supplied connection string or credentials in an exception.
    throw new Error('DATABASE_CONFIGURATION_INVALID');
  }
}

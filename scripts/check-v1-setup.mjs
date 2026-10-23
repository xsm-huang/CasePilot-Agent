import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { parseEnv } from 'node:util';

const projectRoot = fileURLToPath(new URL('..', import.meta.url));
const requiredVariables = [
  'ZHIPU_API_KEY', 'ZHIPU_BASE_URL', 'CHAT_MODEL', 'EMBEDDING_MODEL',
  'EMBEDDING_DIMENSIONS', 'DATABASE_URL', 'POSTGRES_DB', 'POSTGRES_USER',
  'POSTGRES_PASSWORD', 'POSTGRES_PORT',
];

const configured = (value) => typeof value === 'string' && value.trim().length > 0;

/** Values never leave this function; the result contains booleans only. */
export function configurationChecks(environment) {
  const checks = Object.fromEntries(requiredVariables.map((name) => [name, configured(environment[name])]));
  checks.CHAT_MODEL_APPROVED = environment.CHAT_MODEL === 'glm-4.7-flash';
  checks.EMBEDDING_MODEL_APPROVED = environment.EMBEDDING_MODEL === 'embedding-3';
  checks.EMBEDDING_DIMENSIONS_APPROVED = environment.EMBEDDING_DIMENSIONS === '1024';
  checks.POSTGRES_PORT_VALID = /^\d+$/.test(environment.POSTGRES_PORT ?? '')
    && Number(environment.POSTGRES_PORT) > 0 && Number(environment.POSTGRES_PORT) <= 65535;
  try {
    const url = new URL(environment.ZHIPU_BASE_URL);
    checks.ZHIPU_BASE_URL_VALID = url.origin === 'https://open.bigmodel.cn'
      && url.pathname.replace(/\/$/, '') === '/api/paas/v4' && !url.username && !url.password
      && !url.search && !url.hash;
  } catch {
    checks.ZHIPU_BASE_URL_VALID = false;
  }
  try {
    const url = new URL(environment.DATABASE_URL);
    checks.DATABASE_URL_VALID = ['postgres:', 'postgresql:'].includes(url.protocol)
      && ['127.0.0.1', 'localhost'].includes(url.hostname)
      && url.port === environment.POSTGRES_PORT
      && decodeURIComponent(url.username) === environment.POSTGRES_USER
      && decodeURIComponent(url.password) === environment.POSTGRES_PASSWORD
      && decodeURIComponent(url.pathname.slice(1)) === environment.POSTGRES_DB;
  } catch {
    checks.DATABASE_URL_VALID = false;
  }
  return checks;
}

function executeDocker(args, root) {
  return execFileSync('docker', args, {
    cwd: root, encoding: 'utf8', timeout: 15_000, stdio: ['ignore', 'pipe', 'pipe'],
  });
}

/** Only inspect this Compose project. Captured command errors are deliberately not printed. */
export function databaseChecks(root, execute = executeDocker) {
  const checks = { DOCKER_AVAILABLE: false, PROJECT_POSTGRES_RUNNING: false, PGVECTOR_AVAILABLE: false };
  const compose = ['compose', '-p', 'casepilot-agent', '-f', resolve(root, 'compose.yaml')];
  try {
    execute(['info', '--format', '{{.ServerVersion}}'], root);
    checks.DOCKER_AVAILABLE = true;
    const output = execute([...compose, 'ps', '--format', 'json', 'postgres'], root).trim();
    const containers = output.startsWith('[') ? JSON.parse(output) : output.split('\n').filter(Boolean).map(JSON.parse);
    checks.PROJECT_POSTGRES_RUNNING = containers.some((item) => item.Service === 'postgres'
      && item.State === 'running' && item.Health === 'healthy');
    if (!checks.PROJECT_POSTGRES_RUNNING) return checks;
    const sql = "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector'); SELECT '[1,0]'::vector <=> '[1,0]'::vector = 0;";
    const result = execute([...compose, 'exec', '-T', 'postgres', 'sh', '-c',
      'exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc "$1"', '--', sql], root);
    checks.PGVECTOR_AVAILABLE = result.trim().split(/\r?\n/).join(',') === 't,t';
  } catch {
    // Docker diagnostics can contain environment values; expose only the failed checks.
  }
  return checks;
}

export function inspectSetup({ root = projectRoot, environment = process.env, execute } = {}) {
  let localEnvironment = {};
  let envFileExists = false;
  try {
    localEnvironment = parseEnv(readFileSync(resolve(root, '.env'), 'utf8'));
    envFileExists = true;
  } catch {
    // A missing or unreadable local file is a failed prerequisite, never a leaked error.
  }
  const checks = {
    ENV_FILE_EXISTS: envFileExists,
    ...configurationChecks({ ...localEnvironment, ...environment }),
    ...databaseChecks(root, execute),
  };
  return {
    checks,
    setupReady: Object.values(checks).every(Boolean),
    // This read-only check cannot prove provider capability or checkpoint migration.
    providerCapabilitiesVerified: false,
    checkpointPersistenceVerified: false,
    g0Passed: false,
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const result = inspectSetup();
  console.log(JSON.stringify(result, null, 2));
  process.exitCode = result.g0Passed ? 0 : 1;
}

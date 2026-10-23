import assert from 'node:assert/strict';
import { test } from 'node:test';
import { configurationChecks, databaseChecks } from '../../scripts/check-v1-setup.mjs';

const environment = {
  ZHIPU_API_KEY: 'test-only-never-send',
  ZHIPU_BASE_URL: 'https://open.bigmodel.cn/api/paas/v4',
  CHAT_MODEL: 'glm-4.7-flash',
  EMBEDDING_MODEL: 'embedding-3',
  EMBEDDING_DIMENSIONS: '1024',
  POSTGRES_DB: 'casepilot', POSTGRES_USER: 'casepilot', POSTGRES_PASSWORD: 'test-only-password',
  POSTGRES_PORT: '15432',
  DATABASE_URL: 'postgresql://casepilot:test-only-password@127.0.0.1:15432/casepilot',
};

test('configuration inspection reports only booleans and identifies missing credentials', () => {
  assert.ok(Object.values(configurationChecks(environment)).every((value) => value === true));
  const missing = configurationChecks({ ...environment, ZHIPU_API_KEY: ' ' });
  assert.equal(missing.ZHIPU_API_KEY, false);
  assert.ok(Object.values(missing).every((value) => typeof value === 'boolean'));
  assert.equal(JSON.stringify(missing).includes(environment.POSTGRES_PASSWORD), false);
  assert.equal(JSON.stringify(missing).includes(environment.ZHIPU_API_KEY), false);
});

test('configuration inspection rejects profile changes and mismatched database targets', () => {
  const changed = configurationChecks({ ...environment, EMBEDDING_DIMENSIONS: '2048',
    ZHIPU_BASE_URL: 'https://example.com/api/paas/v4', DATABASE_URL: 'not-a-url' });
  assert.equal(changed.EMBEDDING_DIMENSIONS_APPROVED, false);
  assert.equal(changed.ZHIPU_BASE_URL_VALID, false);
  assert.equal(changed.DATABASE_URL_VALID, false);
  assert.equal(configurationChecks({ ...environment, POSTGRES_PORT: '5432' }).DATABASE_URL_VALID, false);
});

test('database inspection confines commands to this project and verifies actual vector operator', () => {
  const commands = [];
  const result = databaseChecks(process.cwd(), (args) => {
    commands.push(args);
    if (args[0] === 'info') return '29.8.0';
    assert.deepEqual(args.slice(0, 3), ['compose', '-p', 'casepilot-agent']);
    if (args.includes('ps')) return '{"Service":"postgres","State":"running","Health":"healthy"}';
    assert.ok(args.includes('exec'));
    assert.match(args.at(-1), /pg_extension/);
    assert.match(args.at(-1), /::vector/);
    return 't\nt\n';
  });
  assert.deepEqual(result, { DOCKER_AVAILABLE: true, PROJECT_POSTGRES_RUNNING: true, PGVECTOR_AVAILABLE: true });
  assert.equal(commands.length, 3);
});

test('failed Docker inspection never exposes captured secrets or claims database success', () => {
  const result = databaseChecks(process.cwd(), () => { throw new Error(environment.POSTGRES_PASSWORD); });
  assert.deepEqual(result, { DOCKER_AVAILABLE: false, PROJECT_POSTGRES_RUNNING: false, PGVECTOR_AVAILABLE: false });
  assert.equal(JSON.stringify(result).includes(environment.POSTGRES_PASSWORD), false);
});

test('unhealthy project does not trigger a database command', () => {
  const result = databaseChecks(process.cwd(), (args) => {
    if (args[0] === 'info') return '29.8.0';
    assert.ok(args.includes('ps'));
    return '[{"Service":"postgres","State":"running","Health":"unhealthy"}]';
  });
  assert.equal(result.PROJECT_POSTGRES_RUNNING, false);
  assert.equal(result.PGVECTOR_AVAILABLE, false);
});

import { spawnSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { compile } from 'json-schema-to-typescript';

// Python models own the transport contract. Commit outputs so the frontend can
// build independently; regenerate after changing a server response model.
const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../..');
const python = process.env.CASEPILOT_PYTHON || resolve(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
const result = spawnSync(python, ['-m', 'casepilot.export_schema'], {
  cwd: root,
  env: { ...process.env, PYTHONPATH: resolve(root, 'apps/api/src'), PYTHONIOENCODING: 'utf-8' },
  encoding: 'utf8',
});
if (result.error) throw result.error;
if (result.status !== 0) throw new Error(result.stderr || 'Python schema export failed');
const schema = JSON.parse(result.stdout);
if (!schema.$defs?.V0AnalysisTask || !schema.$defs?.V0TimelineEvent) throw new Error('Missing Python transport models');
const banner = '// Generated from Python Pydantic models by pnpm --filter @casepilot/contracts generate. Do not edit.\n';
const types = await compile(schema, 'TransportContract', { bannerComment: banner, additionalProperties: false, unreachableDefinitions: true });
const outputs = [
  ['schema/transport.json', JSON.stringify(schema, null, 2) + '\n'],
  ['src/generated/types.ts', types],
  ['src/generated/schema.ts', banner + 'export const transportSchema = ' + JSON.stringify(schema, null, 2) + ' as const;\n'],
];
for (const [relative, content] of outputs) {
  const path = resolve(here, relative);
  if (process.argv.includes('--check')) {
    if (await readFile(path, 'utf8') !== content) throw new Error(`Generated contract is stale: ${relative}`);
  } else {
    await mkdir(dirname(path), { recursive: true });
    await writeFile(path, content, 'utf8');
  }
}

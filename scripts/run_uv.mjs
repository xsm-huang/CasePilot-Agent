import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const bundled = resolve(root, '.tools', 'uv', 'bin', process.platform === 'win32' ? 'uv.exe' : 'uv');
const command = existsSync(bundled) ? bundled : 'uv';
const child = spawn(command, process.argv.slice(2), { cwd: root, stdio: 'inherit' });

child.on('error', (error) => {
  console.error(`Unable to start uv: ${error.message}`);
  console.error('Install uv or place it under .tools/uv/bin.');
  process.exitCode = 1;
});
child.on('exit', (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  else process.exitCode = code ?? 1;
});

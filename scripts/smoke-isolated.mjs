import { spawn } from 'node:child_process';
import { createServer } from 'node:net';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';

const root = fileURLToPath(new URL('..', import.meta.url));
const timeout = AbortSignal.timeout(30_000);
const children = [];

async function availablePort() {
  const reservation = createServer();
  await new Promise((accept, reject) => {
    reservation.once('error', reject);
    reservation.listen(0, '127.0.0.1', accept);
  });
  const address = reservation.address();
  if (typeof address !== 'object' || !address) throw new Error('Could not reserve an isolated port.');
  await new Promise((accept, reject) => reservation.close((error) => error ? reject(error) : accept()));
  return address.port;
}

function start(args, environment) {
  const child = spawn(process.execPath, args, {
    cwd: root, env: { ...process.env, ...environment }, windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  const state = { child, exited: false, code: null, spawnFailed: false };
  state.completion = new Promise((accept) => {
    child.once('error', () => { state.spawnFailed = true; state.exited = true; accept(); });
    child.once('exit', (code) => { state.exited = true; state.code = code; accept(); });
  });
  children.push(state);
  return state;
}

async function stop(state) {
  if (state.exited) return;
  // Only our own spawned child is stopped; no port lookup or process-name matching.
  state.child.kill();
  await Promise.race([state.completion, delay(2000)]);
  if (!state.exited) {
    state.child.kill('SIGKILL');
    await state.completion;
  }
}

try {
  const port = await availablePort();
  const api = start([resolve(root, 'apps/api/dist/main.js')], { PORT: String(port) });
  let listening = false;
  let addressInUse = false;
  let startupOutput = '';
  api.child.stdout.on('data', (chunk) => {
    startupOutput = (startupOutput + String(chunk)).slice(-4000);
    listening ||= startupOutput.includes('CasePilot API running');
  });
  api.child.stderr.on('data', (chunk) => { addressInUse ||= String(chunk).includes('EADDRINUSE'); });
  while (!listening) {
    timeout.throwIfAborted();
    if (api.exited) throw new Error(addressInUse ? 'Isolated port was taken; no existing service was used.'
      : `Compiled API failed to start (exit ${api.code ?? 'spawn failure'}).`);
    await delay(50, undefined, { signal: timeout });
  }
  const base = `http://127.0.0.1:${port}/api`;
  const ready = await fetch(`${base}/cases`, { signal: timeout });
  if (!ready.ok) throw new Error(`Isolated API readiness failed (HTTP ${ready.status}).`);
  const smoke = start([resolve(root, 'scripts/smoke.mjs')], { API_URL: base });
  smoke.child.stdout.on('data', (chunk) => process.stdout.write(chunk));
  while (!smoke.exited) {
    timeout.throwIfAborted();
    if (api.exited) throw new Error('Isolated API stopped during HTTP/SSE verification.');
    await delay(50, undefined, { signal: timeout });
  }
  if (smoke.spawnFailed || smoke.code !== 0) throw new Error(`HTTP/SSE smoke failed (exit ${smoke.code ?? 'spawn failure'}).`);
  console.log('PASS: compiled API verified in its own temporary process; no existing API process was used.');
} catch (error) {
  console.error(timeout.aborted ? 'FAIL: isolated smoke exceeded 30 seconds.'
    : `FAIL: ${error instanceof Error ? error.message : 'isolated smoke failed'}`);
  process.exitCode = 1;
} finally {
  for (const child of children.reverse()) await stop(child);
}

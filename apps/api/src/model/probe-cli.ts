import { loadEnvFile } from 'node:process';
import { fileURLToPath } from 'node:url';
import { ModelConfigurationError, readModelConfig } from './config.js';
import { ModelProbeError, probeModelCapabilities } from './capability-probe.js';

async function main(): Promise<void> {
  if (!process.argv.includes('--live')) {
    console.log('Live verification requires --live and makes up to three small model requests.');
    process.exitCode = 1;
    return;
  }
  try {
    loadEnvFile(fileURLToPath(new URL('../../../../.env', import.meta.url)));
  } catch {
    console.error(JSON.stringify({ verified: false, code: 'LOCAL_ENV_UNAVAILABLE' }));
    process.exitCode = 1;
    return;
  }
  try {
    const result = await probeModelCapabilities(readModelConfig());
    console.log(JSON.stringify({ verified: true, ...result }, null, 2));
  } catch (error) {
    const failure = error instanceof ModelConfigurationError
      ? { code: error.code, field: error.field }
      : error instanceof ModelProbeError
        ? { code: error.code, httpStatus: error.httpStatus }
        : { code: 'UNEXPECTED_PROBE_FAILURE' };
    console.error(JSON.stringify({ verified: false, ...failure }));
    process.exitCode = 1;
  }
}

await main();

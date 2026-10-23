import { loadEnvFile } from 'node:process';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { PostgresSaver } from '@langchain/langgraph-checkpoint-postgres';
import { initializeCheckpointer } from './checkpointer.js';
import { readDatabaseUrl } from './config.js';
import { migrateDatabase } from './migrations.js';
import { createDatabasePool } from './pool.js';
import { Command, createProbeGraph } from './probe-graph.js';

async function main(): Promise<void> {
  const [phase, schemaArg] = process.argv.slice(2);
  if (phase !== '--write' && phase !== '--read') throw new Error('INVALID_PROBE_PHASE');
  const schema = phase === '--write' ? `casepilot_probe_${randomUUID().replaceAll('-', '')}` : schemaArg;
  if (!schema || !/^casepilot_probe_[a-f0-9]{32}$/.test(schema)) throw new Error('INVALID_PROBE_SCHEMA');

  loadEnvFile(fileURLToPath(new URL('../../../../.env', import.meta.url)));
  const pool = createDatabasePool(readDatabaseUrl());
  const config = { configurable: { thread_id: schema } };
  try {
    if (phase === '--write') {
      const migrationVersion = await migrateDatabase(pool);
      await initializeCheckpointer(pool);
      const saver = new PostgresSaver(pool, undefined, { schema });
      await saver.setup();
      const graph = createProbeGraph(saver);
      await graph.invoke({ marker: schema, approved: false }, config);
      const state = await graph.getState(config);
      if (!state.next.includes('review') || state.values.marker !== schema) throw new Error('CHECKPOINT_WRITE_NOT_VERIFIED');
      console.log(JSON.stringify({ phase: 'written', schema, migrationVersion, waitingReview: true }));
    } else {
      // This process did not create the graph state. It must load it from PostgreSQL.
      const saver = new PostgresSaver(pool, undefined, { schema });
      const graph = createProbeGraph(saver);
      const saved = await graph.getState(config);
      if (saved.values.marker !== schema || !saved.next.includes('review')) throw new Error('CHECKPOINT_READ_NOT_VERIFIED');
      await graph.invoke(new Command({ resume: true }), config);
      const resumed = await graph.getState(config);
      if (resumed.values.approved !== true || resumed.next.length !== 0) throw new Error('CHECKPOINT_RESUME_NOT_VERIFIED');
      // Only the validated, isolated probe schema is removed; application/checkpoint schemas remain.
      await pool.query(`DROP SCHEMA "${schema}" CASCADE`);
      console.log(JSON.stringify({ phase: 'verified', crossProcessRead: true, interruptResume: true, probeCleaned: true }));
    }
  } finally {
    await pool.end();
  }
}

try {
  await main();
} catch {
  // Database driver errors can contain connection details. Output a stable code only.
  console.error(JSON.stringify({ verified: false, code: 'DATABASE_PROBE_FAILED' }));
  process.exitCode = 1;
}

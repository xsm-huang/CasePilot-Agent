import { PostgresSaver } from '@langchain/langgraph-checkpoint-postgres';
import type pg from 'pg';

export const checkpointSchema = 'casepilot_checkpoints';

export async function initializeCheckpointer(pool: pg.Pool): Promise<PostgresSaver> {
  const saver = new PostgresSaver(pool, undefined, { schema: checkpointSchema });
  await saver.setup();
  return saver;
}

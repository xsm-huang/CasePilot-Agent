import { z } from 'zod';

export const publicErrorSchema = z.strictObject({
  code: z.string().min(1).max(100),
  message: z.string().min(1).max(2000),
  requestId: z.string().min(1).max(200)
});
export type PublicError = z.infer<typeof publicErrorSchema>;

// Readiness is a cached/local summary. Reading it must never make model requests.
const dependencyReadinessSchema = z.strictObject({
  state: z.enum(['not_configured', 'not_verified', 'ready', 'unavailable']),
  checkedAt: z.iso.datetime().nullable(),
  code: z.string().min(1).max(100).nullable()
});

export const systemReadinessSchema = z.strictObject({
  database: dependencyReadinessSchema,
  pgvector: dependencyReadinessSchema,
  chat: dependencyReadinessSchema,
  embedding: dependencyReadinessSchema
});
export type SystemReadiness = z.infer<typeof systemReadinessSchema>;

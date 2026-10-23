import { z } from 'zod';

const resourceIdSchema = z.string().trim().min(1).max(200);
const revisionSchema = z.number().int().min(0).max(Number.MAX_SAFE_INTEGER);
const questionSchema = z.string().trim().min(1).max(2000);

export const createConversationRequestSchema = z.strictObject({
  title: z.string().trim().min(1).max(200).optional()
});
export type CreateConversationRequest = z.infer<typeof createConversationRequestSchema>;

export const createAnalysisRequestSchema = z.discriminatedUnion('kind', [
  z.strictObject({
    conversationId: resourceIdSchema,
    kind: z.literal('initial'),
    question: questionSchema.optional()
  }),
  z.strictObject({
    conversationId: resourceIdSchema,
    kind: z.literal('followup'),
    question: questionSchema
  })
]);
export type CreateAnalysisRequest = z.infer<typeof createAnalysisRequestSchema>;

export const reviewRequestSchema = z.strictObject({
  decision: z.enum(['approve', 'reject']),
  comment: z.string().trim().max(2000),
  interruptKey: resourceIdSchema,
  expectedRevision: revisionSchema
});
export type ReviewRequest = z.infer<typeof reviewRequestSchema>;

export const recoverRequestSchema = z.strictObject({ expectedRevision: revisionSchema });
export type RecoverRequest = z.infer<typeof recoverRequestSchema>;

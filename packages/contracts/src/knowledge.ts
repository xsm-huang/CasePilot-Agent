import type { V1KnowledgeGeneration, V1KnowledgeRetry } from './generated/types.js';
import { transportValidator } from './transport.js';

export type { V1KnowledgeGeneration, V1KnowledgeAttempt, V1KnowledgeError, V1KnowledgeRetry } from './generated/types.js';
export const v1KnowledgeGenerationSchema = transportValidator<V1KnowledgeGeneration>('V1KnowledgeGeneration');
export const v1KnowledgeRetrySchema = transportValidator<V1KnowledgeRetry>('V1KnowledgeRetry');

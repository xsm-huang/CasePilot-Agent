import { v1KnowledgeGenerationSchema } from '@casepilot/contracts';
import { request } from './http';

export const knowledgeApi = {
  list: (signal: AbortSignal) => request('/knowledge/documents', v1KnowledgeGenerationSchema.array(), { signal }),
  generation: (id: string, signal: AbortSignal) => request(`/knowledge/generations/${encodeURIComponent(id)}`, v1KnowledgeGenerationSchema, { signal }),
  upload: (body: FormData, signal: AbortSignal) => request('/knowledge/documents', v1KnowledgeGenerationSchema, { body, signal }),
  retry: (id: string, expectedRevision: number, key: string, signal: AbortSignal) => request(
    `/knowledge/generations/${encodeURIComponent(id)}/retry`, v1KnowledgeGenerationSchema,
    { body: { expectedRevision }, signal, headers: { 'Idempotency-Key': key } },
  ),
};

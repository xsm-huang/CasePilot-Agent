import assert from 'node:assert/strict';
import { test } from 'node:test';
import { v1KnowledgeGenerationSchema, v1KnowledgeRetrySchema } from '../dist/index.js';

const generation = {
  generationId: 'generation-a', documentId: 'document-a', productCode: 'AUTO-COMPREHENSIVE', clauseVersion: '2025-01',
  fileName: '条款.pdf', sha256: 'a'.repeat(64), status: 'embedding', revision: 3, attempt: 1,
  pageCount: 2, chunkCount: 4, embeddedCount: 2, isActive: false, error: null,
  createdAt: '2026-10-23T01:00:00.000Z', updatedAt: '2026-10-23T01:00:02.000Z',
  attempts: [{ attempt: 1, status: 'embedding', startedAt: '2026-10-23T01:00:00.000Z', finishedAt: null, error: null }],
};

test('knowledge contract preserves separate processing and publication states', () => {
  const ready = { ...generation, status: 'ready', isActive: false };
  assert.equal(v1KnowledgeGenerationSchema.parse(ready).isActive, false);
  assert.equal(v1KnowledgeGenerationSchema.array().parse([generation, ready]).length, 2);
  assert.throws(() => v1KnowledgeGenerationSchema.parse({ ...generation, isActive: 'true' }));
  assert.throws(() => v1KnowledgeGenerationSchema.parse({ ...generation, status: 'published' }));
});

test('knowledge errors and attempt records are checked before rendering', () => {
  assert.throws(() => v1KnowledgeGenerationSchema.parse({ ...generation, error: { message: '未提供错误码' } }));
  assert.throws(() => v1KnowledgeGenerationSchema.parse({ ...generation, attempts: [{ attempt: 1 }] }));
  assert.deepEqual(v1KnowledgeRetrySchema.parse({ expectedRevision: 3 }), { expectedRevision: 3 });
  assert.throws(() => v1KnowledgeRetrySchema.parse({ expectedRevision: 0 }));
  assert.throws(() => v1KnowledgeRetrySchema.parse({ expectedRevision: '3' }));
});

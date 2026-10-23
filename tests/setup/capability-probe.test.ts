import assert from 'node:assert/strict';
import { test, type TestContext } from 'node:test';
import { probeModelCapabilities, ModelProbeError } from '../../apps/api/src/model/capability-probe.ts';
import { readModelConfig } from '../../apps/api/src/model/config.ts';

const config = readModelConfig({ ZHIPU_API_KEY: 'test-only-placeholder' });
const toolOutput = { choices: [{ message: { tool_calls: [{ type: 'function', function: {
  name: 'check_case', arguments: '{"caseId":"DEMO-001"}',
} }] } }] };
const structuredOutput = { choices: [{ message: { content: '{"caseId":"DEMO-001","needsReview":true}' } }] };
const vectorOutput = { data: [{ embedding: Array.from({ length: 1024 }, () => 0.25) }] };

function mockResponses(context: TestContext, responses: unknown[]) {
  const calls: RequestInit[] = [];
  context.mock.method(globalThis, 'fetch', async (_url: string, init: RequestInit) => {
    calls.push(init);
    assert.ok(calls.length <= responses.length, 'unexpected retry or additional provider call');
    return Response.json(responses[calls.length - 1]);
  });
  return calls;
}

function probeError(code: string) {
  return (error: unknown) => error instanceof ModelProbeError && error.code === code;
}

test('capability probe validates all three responses and forbids redirect following', async (context) => {
  const calls = mockResponses(context, [toolOutput, structuredOutput, vectorOutput]);
  const result = await probeModelCapabilities(config);
  assert.equal(result.toolCalling, true);
  assert.equal(result.structuredOutput, true);
  assert.equal(result.embeddingDimensions, 1024);
  assert.equal(calls.length, 3);
  for (const request of calls) {
    assert.equal(request.redirect, 'error');
    assert.equal(request.method, 'POST');
    assert.ok(request.signal instanceof AbortSignal);
  }
  const bodies = calls.map((request) => JSON.parse(String(request.body)));
  assert.equal(bodies[0].model, 'glm-4.7-flash');
  assert.equal(bodies[1].response_format.type, 'json_object');
  assert.equal(bodies[2].model, 'embedding-3');
  assert.equal(bodies[2].dimensions, 1024);
});

test('HTTP 401 stops after one request and does not leak the provider response', async (context) => {
  let count = 0;
  context.mock.method(globalThis, 'fetch', async () => {
    count += 1;
    return new Response('private-provider-response', { status: 401 });
  });
  await assert.rejects(probeModelCapabilities(config), (error: unknown) => {
    assert.ok(error instanceof ModelProbeError);
    assert.equal(error.code, 'MODEL_HTTP_ERROR');
    assert.equal(error.httpStatus, 401);
    assert.equal(error.message.includes('private-provider-response'), false);
    assert.equal(error.message.includes(config.apiKey), false);
    return true;
  });
  assert.equal(count, 1);
});

test('missing tool call fails before JSON and embedding requests', async (context) => {
  const calls = mockResponses(context, [{ choices: [{ message: { content: 'no tool' } }] }]);
  await assert.rejects(probeModelCapabilities(config), probeError('TOOL_CALLING_NOT_VERIFIED'));
  assert.equal(calls.length, 1);
});

test('invalid JSON fails without repair or embedding request', async (context) => {
  const calls = mockResponses(context, [toolOutput, { choices: [{ message: { content: '{broken' } }] }]);
  await assert.rejects(probeModelCapabilities(config), probeError('MODEL_RESPONSE_INVALID'));
  assert.equal(calls.length, 2);
});

test('embedding dimension mismatch cannot produce a verified result', async (context) => {
  const calls = mockResponses(context, [toolOutput, structuredOutput, { data: [{ embedding: [0.25] }] }]);
  await assert.rejects(probeModelCapabilities(config), probeError('EMBEDDING_NOT_VERIFIED'));
  assert.equal(calls.length, 3);
});

test('provider timeouts fail explicitly without retrying', async (context) => {
  let count = 0;
  context.mock.method(globalThis, 'fetch', async () => {
    count += 1;
    throw new DOMException('private-timeout-details', 'TimeoutError');
  });
  await assert.rejects(probeModelCapabilities(config), probeError('MODEL_TIMEOUT'));
  assert.equal(count, 1);
});

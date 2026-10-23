import type { ModelConfig } from './config.js';

export type CapabilityProbeResult = {
  chatModel: string;
  embeddingModel: string;
  embeddingDimensions: number;
  toolCalling: true;
  structuredOutput: true;
  checkedAt: string;
};

export class ModelProbeError extends Error {
  constructor(readonly code: string, readonly httpStatus?: number) {
    super(httpStatus ? `${code} (HTTP ${httpStatus})` : code);
    this.name = 'ModelProbeError';
  }
}

function object(value: unknown): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new ModelProbeError('MODEL_RESPONSE_INVALID');
  }
  return value as Record<string, unknown>;
}

function parseJson(value: unknown): unknown {
  if (typeof value !== 'string') throw new ModelProbeError('MODEL_RESPONSE_INVALID');
  try {
    return JSON.parse(value) as unknown;
  } catch {
    throw new ModelProbeError('MODEL_RESPONSE_INVALID');
  }
}

function firstMessage(response: unknown): Record<string, unknown> {
  const choices = object(response).choices;
  if (!Array.isArray(choices) || choices.length === 0) {
    throw new ModelProbeError('MODEL_RESPONSE_INVALID');
  }
  return object(object(choices[0]).message);
}

/** Exactly three small external requests, no retry. Never call during readiness/startup. */
export async function probeModelCapabilities(config: ModelConfig): Promise<CapabilityProbeResult> {
  async function request(path: string, body: Record<string, unknown>): Promise<unknown> {
    try {
      const response = await fetch(`${config.baseUrl}/${path}`, {
        method: 'POST',
        redirect: 'error',
        headers: {
          Authorization: `Bearer ${config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(config.timeoutMs)
      });
      if (!response.ok) {
        // Provider errors may echo sensitive input. Do not expose their response bodies.
        throw new ModelProbeError('MODEL_HTTP_ERROR', response.status);
      }
      return await response.json() as unknown;
    } catch (error) {
      if (error instanceof ModelProbeError) throw error;
      if (error instanceof Error && (error.name === 'TimeoutError' || error.name === 'AbortError')) {
        throw new ModelProbeError('MODEL_TIMEOUT');
      }
      throw new ModelProbeError('MODEL_REQUEST_FAILED');
    }
  }

  const chatDefaults = {
    model: config.chatModel,
    stream: false,
    max_tokens: 256,
    thinking: { type: 'disabled' }
  };
  const toolResponse = await request('chat/completions', {
    ...chatDefaults,
    messages: [{ role: 'user', content: '请调用 check_case 工具，caseId 必须为 DEMO-001。不要直接回答。' }],
    tool_choice: 'auto',
    tools: [{
      type: 'function',
      function: {
        name: 'check_case',
        description: '检查演示案件',
        parameters: {
          type: 'object',
          properties: { caseId: { type: 'string', enum: ['DEMO-001'] } },
          required: ['caseId'],
          additionalProperties: false
        }
      }
    }]
  });
  const calls = firstMessage(toolResponse).tool_calls;
  if (!Array.isArray(calls) || calls.length !== 1) {
    throw new ModelProbeError('TOOL_CALLING_NOT_VERIFIED');
  }
  const tool = object(calls[0]);
  const fn = object(tool.function);
  const args = object(parseJson(fn.arguments));
  if (tool.type !== 'function' || fn.name !== 'check_case' ||
      args.caseId !== 'DEMO-001' || Object.keys(args).length !== 1) {
    throw new ModelProbeError('TOOL_CALLING_NOT_VERIFIED');
  }

  const structuredResponse = await request('chat/completions', {
    ...chatDefaults,
    messages: [{ role: 'user', content: '仅输出一个 JSON 对象：{"caseId":"DEMO-001","needsReview":true}。不要添加任何其他字段。' }],
    response_format: { type: 'json_object' }
  });
  const result = object(parseJson(firstMessage(structuredResponse).content));
  if (result.caseId !== 'DEMO-001' || result.needsReview !== true || Object.keys(result).length !== 2) {
    throw new ModelProbeError('STRUCTURED_OUTPUT_NOT_VERIFIED');
  }

  const embeddingResponse = await request('embeddings', {
    model: config.embeddingModel,
    input: ['理赔申请需要提供维修费用凭证。'],
    dimensions: config.embeddingDimensions
  });
  const data = object(embeddingResponse).data;
  if (!Array.isArray(data) || data.length !== 1) {
    throw new ModelProbeError('EMBEDDING_NOT_VERIFIED');
  }
  const vector = object(data[0]).embedding;
  if (!Array.isArray(vector) || vector.length !== config.embeddingDimensions ||
      !vector.every(value => typeof value === 'number' && Number.isFinite(value)) ||
      !vector.some(value => value !== 0)) {
    throw new ModelProbeError('EMBEDDING_NOT_VERIFIED');
  }

  return {
    chatModel: config.chatModel,
    embeddingModel: config.embeddingModel,
    embeddingDimensions: config.embeddingDimensions,
    toolCalling: true,
    structuredOutput: true,
    checkedAt: new Date().toISOString()
  };
}

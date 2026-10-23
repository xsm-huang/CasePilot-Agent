export type ModelConfig = Readonly<{
  apiKey: string;
  baseUrl: string;
  chatModel: string;
  embeddingModel: string;
  embeddingDimensions: number;
  timeoutMs: number;
}>;

export class ModelConfigurationError extends Error {
  readonly code = 'MODEL_CONFIGURATION_INVALID';

  constructor(readonly field: string) {
    super(`请检查模型配置项 ${field}`);
    this.name = 'ModelConfigurationError';
  }
}

function positiveInteger(value: string, field: string, max: number): number {
  if (!/^\d+$/.test(value)) throw new ModelConfigurationError(field);
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 1 || parsed > max) {
    throw new ModelConfigurationError(field);
  }
  return parsed;
}

/** Reads values only. The caller loads the root .env before invoking this function. */
export function readModelConfig(env: NodeJS.ProcessEnv = process.env): ModelConfig {
  const apiKey = env.ZHIPU_API_KEY?.trim();
  if (!apiKey || /[\r\n]/.test(apiKey)) throw new ModelConfigurationError('ZHIPU_API_KEY');

  const rawBaseUrl = env.ZHIPU_BASE_URL ?? 'https://open.bigmodel.cn/api/paas/v4';
  let baseUrl: URL;
  try {
    baseUrl = new URL(rawBaseUrl);
  } catch {
    throw new ModelConfigurationError('ZHIPU_BASE_URL');
  }
  // V1 has one provider. Restrict the destination so a mistaken URL cannot receive the key.
  if (baseUrl.origin !== 'https://open.bigmodel.cn' ||
      baseUrl.pathname.replace(/\/$/, '') !== '/api/paas/v4' ||
      baseUrl.username || baseUrl.password || baseUrl.search || baseUrl.hash) {
    throw new ModelConfigurationError('ZHIPU_BASE_URL');
  }

  const chatModel = env.CHAT_MODEL ?? 'glm-4.7-flash';
  const embeddingModel = env.EMBEDDING_MODEL ?? 'embedding-3';
  if (chatModel !== 'glm-4.7-flash') throw new ModelConfigurationError('CHAT_MODEL');
  if (embeddingModel !== 'embedding-3') throw new ModelConfigurationError('EMBEDDING_MODEL');

  const embeddingDimensions = positiveInteger(env.EMBEDDING_DIMENSIONS ?? '1024', 'EMBEDDING_DIMENSIONS', 2048);
  // This deployment has one fixed vector profile; changing it requires an explicit index migration.
  if (embeddingDimensions !== 1024) throw new ModelConfigurationError('EMBEDDING_DIMENSIONS');

  return Object.freeze({
    apiKey,
    baseUrl: baseUrl.toString().replace(/\/$/, ''),
    chatModel,
    embeddingModel,
    embeddingDimensions,
    timeoutMs: positiveInteger(env.MODEL_TIMEOUT_MS ?? '30000', 'MODEL_TIMEOUT_MS', 120000)
  });
}

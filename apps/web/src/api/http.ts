import axios from 'axios';

export interface ResponseSchema<T> { parse(value: unknown): T }

export class ApiError extends Error {
  constructor(readonly status: number, message: string, readonly code?: string, readonly requestId?: string) { super(message); }
}

const api = axios.create({ baseURL: '/api' });

export async function request<T>(path: string, schema: ResponseSchema<T>, options: { body?: unknown; signal?: AbortSignal; headers?: Record<string, string> } = {}): Promise<T> {
  try {
    const response = await api.request<unknown>({
      url: path,
      method: options.body === undefined ? 'GET' : 'POST',
      data: options.body,
      headers: options.headers,
      signal: options.signal
    });
    return schema.parse(response.data);
  } catch (cause) {
    if (!axios.isAxiosError(cause)) throw cause;
    if (cause.code === 'ERR_CANCELED') throw cause;
    const status = cause.response?.status ?? 0;
    const data: unknown = cause.response?.data;
    const message = typeof data === 'object' && data !== null && 'message' in data && typeof data.message === 'string'
      ? data.message
      : status > 0 ? `请求失败：${status}` : '网络请求失败，请检查服务是否可用。';
    const code = typeof data === 'object' && data !== null && 'code' in data && typeof data.code === 'string' ? data.code : undefined;
    const requestId = typeof data === 'object' && data !== null && 'requestId' in data && typeof data.requestId === 'string' ? data.requestId : undefined;
    throw new ApiError(status, message, code, requestId);
  }
}

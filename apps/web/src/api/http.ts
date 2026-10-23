import axios from 'axios';

export interface ResponseSchema<T> { parse(value: unknown): T }

export class ApiError extends Error {
  constructor(readonly status: number, message: string) { super(message); }
}

const api = axios.create({ baseURL: '/api' });

export async function request<T>(path: string, schema: ResponseSchema<T>, options: { body?: unknown; signal?: AbortSignal } = {}): Promise<T> {
  try {
    const response = await api.request<unknown>({
      url: path,
      method: options.body === undefined ? 'GET' : 'POST',
      data: options.body,
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
    throw new ApiError(status, message);
  }
}

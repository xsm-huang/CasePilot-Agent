export interface ResponseSchema<T> { parse(value: unknown): T }

export class ApiError extends Error {
  constructor(readonly status: number, message: string) { super(message); }
}

export async function request<T>(path: string, schema: ResponseSchema<T>, options: { body?: unknown; signal?: AbortSignal } = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    signal: options.signal,
    ...(options.body === undefined ? {} : {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(options.body)
    })
  });
  const data: unknown = await response.json();
  if (!response.ok) {
    const message = typeof data === 'object' && data !== null && 'message' in data && typeof data.message === 'string'
      ? data.message : `请求失败：${response.status}`;
    throw new ApiError(response.status, message);
  }
  return schema.parse(data);
}

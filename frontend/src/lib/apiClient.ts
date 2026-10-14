import type { ApiErrorBody } from '../types/api'

/**
 * Shared typed fetch wrapper. All backend calls go through here so the base URL,
 * credentials, timeouts and error parsing are handled in one place.
 */

export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const DEFAULT_TIMEOUT_MS = 10_000

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details?: unknown

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  return (
    typeof value === 'object' &&
    value !== null &&
    'error' in value &&
    typeof (value as ApiErrorBody).error?.message === 'string'
  )
}

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  timeoutMs?: number
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, timeoutMs = DEFAULT_TIMEOUT_MS, headers, signal, ...rest } = options
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  signal?.addEventListener('abort', () => controller.abort())

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      credentials: 'same-origin',
      headers: {
        Accept: 'application/json',
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })
  } catch (cause) {
    const aborted = cause instanceof DOMException && cause.name === 'AbortError'
    throw new ApiError(
      0,
      aborted ? 'timeout' : 'network_error',
      aborted ? 'The server took too long to respond.' : 'Could not reach the NutriPlan API.',
    )
  } finally {
    clearTimeout(timer)
  }

  const payload: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    if (isApiErrorBody(payload)) {
      throw new ApiError(
        response.status,
        payload.error.code,
        payload.error.message,
        payload.error.details,
      )
    }
    throw new ApiError(response.status, 'http_error', `Request failed with status ${response.status}.`)
  }
  return payload as T
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) => apiRequest<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'PUT', body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'DELETE' }),
}

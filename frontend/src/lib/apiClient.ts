import type { ApiErrorBody } from '../types/api'

/**
 * Shared typed fetch wrapper. All backend calls go through here so the base URL,
 * cookies, CSRF header, timeouts and error parsing are handled in one place.
 */

export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const DEFAULT_TIMEOUT_MS = 15_000
const CSRF_COOKIE = 'np_csrf'
const CSRF_HEADER = 'X-CSRF-Token'
const UNSAFE = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

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

export function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  for (const part of document.cookie.split(';')) {
    const [key, ...rest] = part.trim().split('=')
    if (key === name) return decodeURIComponent(rest.join('='))
  }
  return null
}

let csrfRequest: Promise<string> | null = null

/** Double-submit CSRF token: the cookie value echoed in a header (backend/app/core/csrf.py). */
async function csrfToken(): Promise<string> {
  const existing = readCookie(CSRF_COOKIE)
  if (existing) return existing
  csrfRequest ??= rawRequest<{ csrf_token: string }>('/auth/csrf', { method: 'GET' })
    .then((r) => readCookie(CSRF_COOKIE) ?? r.csrf_token)
    .finally(() => {
      csrfRequest = null
    })
  return csrfRequest
}

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  timeoutMs?: number
}

async function rawRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
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

  if (response.status === 204) return undefined as T
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

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = (options.method ?? 'GET').toUpperCase()
  if (!UNSAFE.has(method)) return rawRequest<T>(path, options)
  const token = await csrfToken()
  return rawRequest<T>(path, { ...options, headers: { ...options.headers, [CSRF_HEADER]: token } })
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

/** Maps a 422 response to `{ fieldName: message }` for inline form errors (REQ-4.1.4). */
export function fieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError) || !Array.isArray(error.details)) return {}
  const result: Record<string, string> = {}
  for (const item of error.details as Array<{ location?: unknown[]; message?: string }>) {
    const loc = item.location ?? []
    const field = loc[loc.length - 1]
    if (typeof field === 'string' && item.message) result[field] = item.message
  }
  return result
}

export function errorMessage(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  return error instanceof Error && error.message ? error.message : fallback
}

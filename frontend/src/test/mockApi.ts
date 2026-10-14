import { vi } from 'vitest'

import type { HealthResponse, SessionResponse, User } from '../types/api'

export const HEALTHY: HealthResponse = {
  status: 'ok',
  service: 'NutriPlan API',
  version: '0.1.0',
  environment: 'test',
  database: 'ok',
}

export const USER: User = {
  id: 1,
  email: 'asha@example.com',
  full_name: 'Asha Rao',
  role: 'user',
  created_at: '2026-10-01T10:00:00Z',
}

export const ADMIN: User = { ...USER, id: 2, email: 'admin@example.com', full_name: 'Admin', role: 'admin' }

export function session(user: User = USER, hasProfile = true): SessionResponse {
  return { user, has_profile: hasProfile }
}

type Handler = (init: RequestInit & { url: string }) => unknown
export interface MockRoute {
  status?: number
  body?: unknown
  handler?: Handler
}

export interface ApiCall {
  method: string
  path: string
  body: unknown
  headers: Record<string, string>
}

/**
 * Route values are either a raw JSON body or a MockRoute ({ status?, body?, handler? }).
 * Wrap bodies that themselves contain a "status" or "body" key in { body: ... }.
 *
 * Installs a fetch mock keyed by "METHOD /path" (path relative to /api/v1).
 * Unknown routes return 404 with the backend error shape. Returns the call log.
 */
export function mockApi(routes: Record<string, MockRoute | unknown> = {}, opts: { user?: User | null } = {}) {
  const calls: ApiCall[] = []
  const defaults: Record<string, MockRoute> = {
    'GET /health': { body: HEALTHY },
    'GET /auth/csrf': { body: { csrf_token: 'test-csrf' } },
    'GET /auth/me':
      opts.user === undefined || opts.user === null
        ? { status: 401, body: { error: { code: 'unauthorized', message: 'Please log in to continue.' } } }
        : { body: session(opts.user) },
  }
  document.cookie = 'np_csrf=test-csrf; path=/'

  const fetchMock = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = typeof input === 'string' ? input : input.toString()
    const path = url.replace(/^\/api\/v1/, '').split('?')[0]
    const method = (init.method ?? 'GET').toUpperCase()
    const body = typeof init.body === 'string' ? JSON.parse(init.body) : undefined
    calls.push({ method, path, body, headers: (init.headers ?? {}) as Record<string, string> })

    const key = `${method} ${path}`
    const raw = key in routes ? routes[key] : defaults[key]
    if (raw === undefined) {
      return new Response(JSON.stringify({ error: { code: 'not_found', message: 'Not Found' } }), {
        status: 404,
      })
    }
    const route: MockRoute =
      typeof raw === 'object' && raw !== null && ('body' in raw || 'status' in raw || 'handler' in raw)
        ? (raw as MockRoute)
        : { body: raw }
    const payload = route.handler ? route.handler({ ...init, url }) : route.body
    const status = route.status ?? 200
    return new Response(status === 204 ? null : JSON.stringify(payload ?? null), { status })
  })
  vi.stubGlobal('fetch', fetchMock)
  return calls
}

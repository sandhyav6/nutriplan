import { describe, expect, it, vi } from 'vitest'

import { API_BASE_URL, ApiError, apiClient, fieldErrors } from './apiClient'

function clearCsrfCookie() {
  document.cookie = 'np_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'
}

describe('apiClient', () => {
  it('prefixes requests with the versioned API base URL', async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ ok: true }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    await expect(apiClient.get('/health')).resolves.toEqual({ ok: true })
    expect(API_BASE_URL).toBe('/api/v1')
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/health', expect.objectContaining({ method: 'GET', credentials: 'same-origin' }))
  })

  it('turns backend error bodies into ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ error: { code: 'not_found', message: 'Not Found' } }), { status: 404 })),
    )
    const error = await apiClient.get('/missing').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 404, code: 'not_found', message: 'Not Found' })
  })

  it('reports network failures as ApiError with status 0', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))))
    await expect(apiClient.get('/health')).rejects.toMatchObject({ status: 0, code: 'network_error' })
  })

  it('fetches a CSRF token first and sends it on state-changing requests', async () => {
    clearCsrfCookie()
    const fetchMock = vi.fn(async (url: string) => {
      if (url.endsWith('/auth/csrf')) {
        document.cookie = 'np_csrf=fresh-token; path=/'
        return new Response(JSON.stringify({ csrf_token: 'fresh-token' }), { status: 200 })
      }
      return new Response('{}', { status: 200 })
    })
    vi.stubGlobal('fetch', fetchMock)
    await apiClient.post('/example', { a: 1 })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/auth/csrf')
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/v1/example',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ a: 1 }),
        headers: expect.objectContaining({ 'Content-Type': 'application/json', 'X-CSRF-Token': 'fresh-token' }),
      }),
    )
  })

  it('returns undefined for 204 responses', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(null, { status: 204 })))
    await expect(apiClient.delete('/thing')).resolves.toBeUndefined()
  })

  it('maps validation details to field errors', () => {
    const error = new ApiError(422, 'validation_error', 'bad', [{ location: ['body', 'age'], message: 'Too young' }])
    expect(fieldErrors(error)).toEqual({ age: 'Too young' })
  })
})

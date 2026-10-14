import { describe, expect, it, vi } from 'vitest'

import { API_BASE_URL, ApiError, apiClient } from './apiClient'

describe('apiClient', () => {
  it('prefixes requests with the versioned API base URL', async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ ok: true }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiClient.get('/health')).resolves.toEqual({ ok: true })
    expect(API_BASE_URL).toBe('/api/v1')
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/health', expect.objectContaining({ method: 'GET' }))
  })

  it('turns backend error bodies into ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(JSON.stringify({ error: { code: 'not_found', message: 'Not Found' } }), {
            status: 404,
          }),
      ),
    )

    const error = await apiClient.get('/missing').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 404, code: 'not_found', message: 'Not Found' })
  })

  it('reports network failures as ApiError with status 0', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))))
    await expect(apiClient.get('/health')).rejects.toMatchObject({ status: 0, code: 'network_error' })
  })

  it('serialises JSON bodies', async () => {
    const fetchMock = vi.fn(async () => new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    await apiClient.post('/example', { a: 1 })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/example',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ a: 1 }),
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      }),
    )
  })
})

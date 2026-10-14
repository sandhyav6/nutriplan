import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { HEALTHY, mockApi } from '../../test/mockApi'
import { ApiStatusIndicator } from './ApiStatusIndicator'

describe('ApiStatusIndicator', () => {
  it('shows online when the health endpoint responds', async () => {
    render(<ApiStatusIndicator pollMs={0} />)
    expect(await screen.findByText('API online')).toBeInTheDocument()
  })

  it('flags an unavailable database', async () => {
    mockApi({ 'GET /health': { body: { ...HEALTHY, status: 'degraded', database: 'unavailable' } } })
    render(<ApiStatusIndicator pollMs={0} />)
    expect(await screen.findByText(/database unavailable/i)).toBeInTheDocument()
  })

  it('shows offline when the API cannot be reached', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))))
    render(<ApiStatusIndicator pollMs={0} />)
    expect(await screen.findByText('API offline')).toBeInTheDocument()
  })
})

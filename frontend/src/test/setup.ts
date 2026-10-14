import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

import type { HealthResponse } from '../types/api'

export const HEALTHY: HealthResponse = {
  status: 'ok',
  service: 'NutriPlan API',
  version: '0.1.0',
  environment: 'test',
  database: 'ok',
}

beforeEach(() => {
  // Default: every fetch answers like a healthy backend. Individual tests can override.
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(JSON.stringify(HEALTHY), { status: 200 })),
  )
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

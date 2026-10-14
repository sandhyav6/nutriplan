import { useCallback, useEffect, useState } from 'react'

import { fetchHealth } from '../features/health/api'
import type { HealthResponse } from '../types/api'

export type ApiHealthState =
  | { status: 'loading' }
  | { status: 'online'; data: HealthResponse }
  | { status: 'offline'; message: string }

/** Polls the real FastAPI health endpoint. */
export function useApiHealth(pollMs = 30_000): ApiHealthState & { refresh: () => void } {
  const [state, setState] = useState<ApiHealthState>({ status: 'loading' })
  const [tick, setTick] = useState(0)

  const refresh = useCallback(() => setTick((t) => t + 1), [])

  useEffect(() => {
    const controller = new AbortController()
    fetchHealth(controller.signal)
      .then((data) => setState({ status: 'online', data }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        setState({
          status: 'offline',
          message: error instanceof Error ? error.message : 'Could not reach the API.',
        })
      })
    const timer = pollMs > 0 ? setInterval(() => setTick((t) => t + 1), pollMs) : undefined
    return () => {
      controller.abort()
      if (timer) clearInterval(timer)
    }
  }, [tick, pollMs])

  return { ...state, refresh }
}

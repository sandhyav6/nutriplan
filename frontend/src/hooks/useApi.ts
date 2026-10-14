import { useCallback, useEffect, useState } from 'react'

import { apiClient, ApiError } from '../lib/apiClient'

export type ApiResource<T> =
  | { status: 'loading'; data: null; error: null }
  | { status: 'success'; data: T; error: null }
  | { status: 'error'; data: null; error: ApiError }

/** Loads `path` with the shared API client; `reload()` fetches again. */
export function useApi<T>(path: string | null) {
  const [state, setState] = useState<ApiResource<T>>({ status: 'loading', data: null, error: null })
  const [tick, setTick] = useState(0)
  const reload = useCallback(() => setTick((t) => t + 1), [])

  useEffect(() => {
    if (path === null) return
    const controller = new AbortController()
    apiClient
      .get<T>(path, { signal: controller.signal })
      .then((data) => setState({ status: 'success', data, error: null }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        const apiError =
          error instanceof ApiError ? error : new ApiError(0, 'unknown', 'Something went wrong.')
        setState({ status: 'error', data: null, error: apiError })
      })
    return () => controller.abort()
  }, [path, tick])

  const setData = useCallback((data: T) => setState({ status: 'success', data, error: null }), [])
  return { ...state, reload, setData }
}

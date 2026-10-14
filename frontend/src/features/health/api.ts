import { apiClient } from '../../lib/apiClient'
import type { HealthResponse } from '../../types/api'

export function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiClient.get<HealthResponse>('/health', { signal, timeoutMs: 5_000 })
}

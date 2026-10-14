/** Shape of every error returned by the FastAPI backend (backend/app/core/errors.py). */
export interface ApiErrorBody {
  error: {
    code: string
    message: string
    details?: unknown
  }
}

/** GET /api/v1/health (backend/app/schemas/health.py). */
export interface HealthResponse {
  status: 'ok' | 'degraded'
  service: string
  version: string
  environment: string
  database: 'ok' | 'unavailable'
}

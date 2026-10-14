import { useApiHealth } from '../../hooks/useApiHealth'
import { cn } from '../../lib/cn'

/** Live connectivity indicator backed by GET /api/v1/health. */
export function ApiStatusIndicator({ pollMs }: { pollMs?: number }) {
  const health = useApiHealth(pollMs)

  let tone = 'bg-stone-400'
  let label = 'Checking API…'
  let detail = ''
  if (health.status === 'online') {
    const dbOk = health.data.database === 'ok'
    tone = dbOk ? 'bg-brand-500' : 'bg-amber-500'
    label = dbOk ? 'API online' : 'API online · database unavailable'
    detail = `${health.data.service} v${health.data.version} (${health.data.environment})`
  } else if (health.status === 'offline') {
    tone = 'bg-danger-700'
    label = 'API offline'
    detail = health.message
  }

  return (
    <div className="flex items-center gap-2 text-sm text-ink-muted" role="status" aria-live="polite">
      <span className={cn('inline-block h-2.5 w-2.5 shrink-0 rounded-full', tone)} aria-hidden="true" />
      <span className="font-medium text-ink">{label}</span>
      {detail && <span className="hidden truncate sm:inline">— {detail}</span>}
      {health.status !== 'loading' && (
        <button
          type="button"
          onClick={health.refresh}
          className="ml-1 rounded px-1.5 py-0.5 text-xs font-medium text-brand-700 underline-offset-2 hover:underline"
        >
          Recheck
        </button>
      )}
    </div>
  )
}

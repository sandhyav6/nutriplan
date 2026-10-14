import { cn } from '../../lib/cn'

/** Horizontal progress meter, e.g. spend vs budget. Turns amber when over the limit. */
export function Meter({ value, max, label }: { value: number; max: number; label: string }) {
  const ratio = max > 0 ? value / max : 0
  const over = ratio > 1
  return (
    <div
      role="meter"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={Math.round(value)}
      className="h-2.5 w-full overflow-hidden rounded-full bg-surface-muted"
    >
      <div
        className={cn('h-full rounded-full', over ? 'bg-amber-500' : 'bg-brand-500')}
        style={{ width: `${Math.min(100, ratio * 100)}%` }}
      />
    </div>
  )
}

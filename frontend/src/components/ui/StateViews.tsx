import type { ReactNode } from 'react'

import { cn } from '../../lib/cn'

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-8 text-sm text-ink-muted" role="status">
      <span
        className="h-4 w-4 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600"
        aria-hidden="true"
      />
      {label}
    </div>
  )
}

export function EmptyState({
  title,
  children,
  action,
  className,
}: {
  title: string
  children?: ReactNode
  action?: ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        'flex flex-col items-center rounded-2xl border border-dashed border-line bg-surface/60 px-6 py-10 text-center',
        className,
      )}
    >
      <p className="font-semibold text-ink">{title}</p>
      {children && <div className="mt-2 max-w-md text-sm leading-relaxed text-ink-muted">{children}</div>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function ErrorState({ title = 'Something went wrong', message }: { title?: string; message: string }) {
  return (
    <div role="alert" className="rounded-xl border border-danger-200 bg-danger-50 px-4 py-3 text-sm text-danger-700">
      <p className="font-semibold">{title}</p>
      <p className="mt-1">{message}</p>
    </div>
  )
}

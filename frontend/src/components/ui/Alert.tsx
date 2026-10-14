import type { ReactNode } from 'react'

import { cn } from '../../lib/cn'

type Tone = 'info' | 'success' | 'warning' | 'error'

const tones: Record<Tone, string> = {
  info: 'border-brand-200 bg-brand-50 text-brand-800',
  success: 'border-brand-200 bg-brand-50 text-brand-800',
  warning: 'border-caution-200 bg-caution-50 text-caution-800',
  error: 'border-danger-200 bg-danger-50 text-danger-700',
}

const icons: Record<Tone, string> = { info: 'ℹ', success: '✓', warning: '!', error: '✕' }

export function Alert({
  tone = 'info',
  title,
  children,
  className,
}: {
  tone?: Tone
  title?: string
  children?: ReactNode
  className?: string
}) {
  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={cn('flex gap-3 rounded-xl border px-4 py-3 text-sm', tones[tone], className)}
    >
      <span aria-hidden="true" className="font-bold">
        {icons[tone]}
      </span>
      <div className="min-w-0">
        {title && <p className="font-semibold">{title}</p>}
        {children && <div className={cn('leading-relaxed', title && 'mt-0.5')}>{children}</div>}
      </div>
    </div>
  )
}

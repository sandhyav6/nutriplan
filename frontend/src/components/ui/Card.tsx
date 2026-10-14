import type { HTMLAttributes, ReactNode } from 'react'

import { cn } from '../../lib/cn'

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('rounded-2xl border border-line bg-surface p-5 shadow-sm sm:p-6', className)}
      {...props}
    />
  )
}

export function CardTitle({ children, className }: { children: ReactNode; className?: string }) {
  return <h2 className={cn('text-lg font-semibold text-ink', className)}>{children}</h2>
}

export function CardDescription({ children }: { children: ReactNode }) {
  return <p className="mt-1 text-sm leading-relaxed text-ink-muted">{children}</p>
}

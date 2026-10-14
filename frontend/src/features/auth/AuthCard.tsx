import type { ReactNode } from 'react'

import { Card } from '../../components/ui/Card'

/** Centered card used by the login and registration screens. */
export function AuthCard({
  title,
  description,
  children,
  footer,
}: {
  title: string
  description: string
  children: ReactNode
  footer: ReactNode
}) {
  return (
    <div className="mx-auto w-full max-w-md">
      <Card>
        <h1 className="text-2xl font-bold tracking-tight text-ink">{title}</h1>
        <p className="mt-1 text-sm text-ink-muted">{description}</p>
        <div className="mt-6 space-y-4">{children}</div>
      </Card>
      <p className="mt-4 text-center text-sm text-ink-muted">{footer}</p>
    </div>
  )
}

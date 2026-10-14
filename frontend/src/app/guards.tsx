import type { ReactNode } from 'react'
import { Navigate, useLocation, useSearchParams } from 'react-router'

import { EmptyState, LoadingState } from '../components/ui/StateViews'
import { ButtonLink } from '../components/ui/Button'
import { useAuth } from '../hooks/useAuth'
import { safeNext } from '../lib/safeNext'

/** Private pages: redirect anonymous visitors to the login page (SRS §5.3). */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { state } = useAuth()
  const location = useLocation()
  if (state.status === 'loading') return <LoadingState label="Checking your session…" />
  if (state.status === 'anonymous') {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }
  return <>{children}</>
}

/** Admin pages: the backend enforces the role too – this only avoids showing a broken page. */
export function RequireAdmin({ children }: { children: ReactNode }) {
  const { state } = useAuth()
  if (state.status === 'authenticated' && state.user.role !== 'admin') {
    return (
      <EmptyState
        title="Administrator access required"
        action={<ButtonLink to="/dashboard">Back to dashboard</ButtonLink>}
      >
        The admin panel is only available to NutriPlan administrators.
      </EmptyState>
    )
  }
  return <RequireAuth>{children}</RequireAuth>
}

/** Login / register: signed-in users go straight to the app. */
export function GuestOnly({ children }: { children: ReactNode }) {
  const { state } = useAuth()
  const [params] = useSearchParams()
  if (state.status === 'loading') return <LoadingState label="Checking your session…" />
  if (state.status === 'authenticated') {
    const fallback = state.hasProfile ? '/dashboard' : '/profile'
    return <Navigate to={safeNext(params.get('next')) ?? fallback} replace />
  }
  return <>{children}</>
}

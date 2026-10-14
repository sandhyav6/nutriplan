import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { apiClient } from '../../lib/apiClient'
import type { SessionResponse } from '../../types/api'
import { AuthContext, type AuthContextValue, type AuthState } from './authContext'

const LOADING: AuthState = { status: 'loading', user: null, hasProfile: false }
const ANONYMOUS: AuthState = { status: 'anonymous', user: null, hasProfile: false }

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(LOADING)

  const apply = useCallback((session: SessionResponse) => {
    setState({ status: 'authenticated', user: session.user, hasProfile: session.has_profile })
    return session
  }, [])

  const refresh = useCallback(async () => {
    try {
      apply(await apiClient.get<SessionResponse>('/auth/me'))
    } catch {
      setState(ANONYMOUS) // 401 (not logged in) or API unreachable
    }
  }, [apply])

  // Restore the session on first load (the cookie is HttpOnly, so ask the server).
  useEffect(() => {
    let active = true
    apiClient
      .get<SessionResponse>('/auth/me')
      .then((session) => active && apply(session))
      .catch(() => active && setState(ANONYMOUS))
    return () => {
      active = false
    }
  }, [apply])

  const value = useMemo<AuthContextValue>(
    () => ({
      state,
      refresh,
      login: async (email, password) =>
        apply(await apiClient.post<SessionResponse>('/auth/login', { email, password })),
      register: async (fullName, email, password) =>
        apply(
          await apiClient.post<SessionResponse>('/auth/register', {
            full_name: fullName,
            email,
            password,
          }),
        ),
      logout: async () => {
        try {
          await apiClient.post('/auth/logout')
        } finally {
          setState(ANONYMOUS)
        }
      },
      setHasProfile: (hasProfile) =>
        setState((s) => (s.status === 'authenticated' ? { ...s, hasProfile } : s)),
    }),
    [state, refresh, apply],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

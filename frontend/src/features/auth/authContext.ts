import { createContext } from 'react'

import type { SessionResponse, User } from '../../types/api'

export type AuthState =
  | { status: 'loading'; user: null; hasProfile: false }
  | { status: 'anonymous'; user: null; hasProfile: false }
  | { status: 'authenticated'; user: User; hasProfile: boolean }

export interface AuthContextValue {
  state: AuthState
  login: (email: string, password: string) => Promise<SessionResponse>
  register: (fullName: string, email: string, password: string) => Promise<SessionResponse>
  logout: () => Promise<void>
  refresh: () => Promise<void>
  setHasProfile: (value: boolean) => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

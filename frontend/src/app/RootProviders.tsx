import { Outlet } from 'react-router'

import { AuthProvider } from '../features/auth/AuthProvider'

/** App-wide providers that need router context. */
export function RootProviders() {
  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  )
}

import { Outlet } from 'react-router'

import { SiteFooter } from './SiteFooter'
import { SiteHeader } from './SiteHeader'

export function AppLayout() {
  return (
    <div className="flex min-h-dvh flex-col">
      <a
        href="#main"
        className="sr-only z-30 rounded-lg bg-brand-600 px-3 py-2 text-white focus:not-sr-only focus:absolute focus:top-3 focus:left-3"
      >
        Skip to content
      </a>
      <SiteHeader />
      <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 sm:py-10">
        <Outlet />
      </main>
      <SiteFooter />
    </div>
  )
}

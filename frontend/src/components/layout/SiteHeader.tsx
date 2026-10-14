import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router'

import { useAuth } from '../../hooks/useAuth'
import { cn } from '../../lib/cn'
import { buttonClasses } from '../ui/buttonStyles'

const USER_NAV = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/meal-plan', label: 'Meal Plan' },
  { to: '/grocery-list', label: 'Grocery List' },
  { to: '/profile', label: 'Profile' },
  { to: '/help', label: 'Help' },
] as const

function navClass({ isActive }: { isActive: boolean }) {
  return cn(
    'rounded-lg px-3 py-2 text-sm font-medium transition-colors',
    isActive ? 'bg-brand-50 text-brand-800' : 'text-ink-muted hover:bg-surface-muted hover:text-ink',
  )
}

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 rounded-lg font-bold text-ink">
      <img src="/favicon.svg" alt="" className="h-8 w-8" />
      <span className="text-lg tracking-tight">NutriPlan</span>
    </Link>
  )
}

export function SiteHeader() {
  const [open, setOpen] = useState(false)
  const { state, logout } = useAuth()
  const navigate = useNavigate()
  const signedIn = state.status === 'authenticated'
  const items = signedIn
    ? [...USER_NAV, ...(state.user.role === 'admin' ? [{ to: '/admin', label: 'Admin' }] : [])]
    : [{ to: '/help', label: 'Help' }]

  async function handleLogout() {
    setOpen(false)
    await logout()
    navigate('/login', { replace: true })
  }

  const accountActions = signedIn ? (
    <>
      <span className="hidden max-w-[12rem] truncate text-sm text-ink-muted lg:inline" title={state.user.email}>
        {state.user.full_name}
      </span>
      <button type="button" onClick={handleLogout} className={buttonClasses('secondary', 'sm')}>
        Log out
      </button>
    </>
  ) : (
    <>
      <Link to="/login" className={buttonClasses('ghost', 'sm')} onClick={() => setOpen(false)}>
        Log in
      </Link>
      <Link to="/register" className={buttonClasses('primary', 'sm')} onClick={() => setOpen(false)}>
        Get started
      </Link>
    </>
  )

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-canvas/90 backdrop-blur print:hidden">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Logo />

        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {items.map((item) => (
            <NavLink key={item.to} to={item.to} className={navClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">{accountActions}</div>

        <button
          type="button"
          className="rounded-lg p-2 text-ink md:hidden"
          aria-expanded={open}
          aria-controls="mobile-nav"
          aria-label={open ? 'Close menu' : 'Open menu'}
          onClick={() => setOpen((v) => !v)}
        >
          <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2">
            {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
          </svg>
        </button>
      </div>

      {open && (
        <nav id="mobile-nav" aria-label="Mobile" className="border-t border-line px-4 py-3 md:hidden">
          <div className="flex flex-col gap-1">
            {items.map((item) => (
              <NavLink key={item.to} to={item.to} className={navClass} onClick={() => setOpen(false)}>
                {item.label}
              </NavLink>
            ))}
            <div className="mt-2 flex items-center gap-2 border-t border-line pt-3">{accountActions}</div>
          </div>
        </nav>
      )}
    </header>
  )
}

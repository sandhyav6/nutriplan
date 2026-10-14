import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { mockApi, USER } from '../../test/mockApi'
import { renderRoute } from '../../test/renderRoute'

describe('AppLayout', () => {
  it('renders landmarks, skip link and the medical disclaimer', async () => {
    renderRoute('/help')
    expect(await screen.findByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByRole('contentinfo')).toHaveTextContent(/not medical advice/i)
    expect(screen.getByRole('link', { name: /skip to content/i })).toHaveAttribute('href', '#main')
  })

  it('marks the active navigation link for signed-in users', async () => {
    mockApi({ 'GET /meal-plans/current': { status: 404, body: { error: { code: 'plan_not_found', message: 'No plan' } } } }, { user: USER })
    renderRoute('/meal-plan')
    const nav = await screen.findByRole('navigation', { name: 'Main' })
    await waitFor(() => expect(nav.querySelector('a[aria-current="page"]')).toHaveTextContent('Meal Plan'))
  })

  it('logs out and returns to the login page', async () => {
    const calls = mockApi({ 'POST /auth/logout': { status: 204 }, 'GET /dashboard': { status: 500, body: { error: { code: 'x', message: 'x' } } } }, { user: USER })
    const { router } = renderRoute('/dashboard')
    await userEvent.click(await screen.findByRole('button', { name: 'Log out' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    const logout = calls.find((c) => c.path === '/auth/logout')
    expect(logout?.headers['X-CSRF-Token']).toBe('test-csrf')
  })

  it('toggles the mobile menu', async () => {
    renderRoute('/')
    const toggle = await screen.findByRole('button', { name: /open menu/i })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(toggle)
    expect(screen.getByRole('navigation', { name: 'Mobile' })).toBeInTheDocument()
  })
})

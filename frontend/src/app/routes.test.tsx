import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { DASHBOARD, GROCERY, PLAN, PROFILE } from '../test/fixtures'
import { ADMIN, mockApi, USER } from '../test/mockApi'
import { renderRoute } from '../test/renderRoute'

describe('routing and access control', () => {
  it('renders the public home page for visitors', async () => {
    renderRoute('/')
    expect(await screen.findByRole('heading', { level: 1, name: /healthy weekly meals/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Create an account' })).toHaveAttribute('href', '/register')
  })

  it.each(['/dashboard', '/meal-plan', '/grocery-list', '/profile', '/admin', '/meal-plan/meals/3'])(
    'redirects anonymous visitors from %s to login (SRS §5.3)',
    async (path) => {
      const { router } = renderRoute(path)
      expect(await screen.findByRole('heading', { name: 'Log in' })).toBeInTheDocument()
      expect(router.state.location.pathname).toBe('/login')
      expect(router.state.location.search).toBe(`?next=${encodeURIComponent(path)}`)
    },
  )

  it('help page is public', async () => {
    renderRoute('/help')
    expect(await screen.findByRole('heading', { level: 1, name: /help/i })).toBeInTheDocument()
  })

  it('signed-in users reach their pages', async () => {
    mockApi(
      {
        'GET /dashboard': DASHBOARD,
        'GET /meal-plans/current': PLAN,
        'GET /grocery-lists/current': GROCERY,
        'GET /profile': PROFILE,
        'GET /allergens': [{ id: 1, name: 'Peanuts' }],
        'GET /foods': [],
      },
      { user: USER },
    )
    const { router } = renderRoute('/dashboard')
    expect(await screen.findByRole('heading', { name: 'Hello, Asha' })).toBeInTheDocument()
    const nav = screen.getByRole('navigation', { name: 'Main' })
    expect(within(nav).queryByRole('link', { name: 'Admin' })).not.toBeInTheDocument()
    await userEvent.click(within(nav).getByRole('link', { name: 'Grocery List' }))
    expect(router.state.location.pathname).toBe('/grocery-list')
    expect(await screen.findByText('1.25 kg')).toBeInTheDocument()
  })

  it('logged-in users are sent away from login', async () => {
    mockApi({}, { user: USER })
    const { router } = renderRoute('/login')
    await waitFor(() => expect(router.state.location.pathname).toBe('/dashboard'))
  })

  it('admin route is denied to normal users', async () => {
    mockApi({}, { user: USER })
    renderRoute('/admin')
    expect(await screen.findByText('Administrator access required')).toBeInTheDocument()
  })

  it('admins see the admin panel and nav link', async () => {
    mockApi({ 'GET /admin/foods': [], 'GET /admin/food-groups': [], 'GET /allergens': [] }, { user: ADMIN })
    renderRoute('/admin')
    expect(await screen.findByRole('heading', { level: 1, name: 'Admin panel' })).toBeInTheDocument()
    expect(within(screen.getByRole('navigation', { name: 'Main' })).getByRole('link', { name: 'Admin' })).toBeInTheDocument()
    expect(screen.getAllByRole('tab')).toHaveLength(4)
  })

  it('shows a 404 page for unknown routes', async () => {
    renderRoute('/does-not-exist')
    expect(await screen.findByText(/404 – page not found/i)).toBeInTheDocument()
  })
})

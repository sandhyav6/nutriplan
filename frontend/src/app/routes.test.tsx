import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { renderRoute } from '../test/renderRoute'

describe('application routing', () => {
  it('renders the home page', async () => {
    renderRoute('/')
    expect(
      screen.getByRole('heading', { level: 1, name: /healthy weekly meals/i }),
    ).toBeInTheDocument()
    await waitFor(() => expect(screen.getAllByText('API online').length).toBeGreaterThan(0))
  })

  it.each([
    ['/login', /log in/i],
    ['/register', /create your account/i],
    ['/profile', /set up your nutrition profile/i],
    ['/meal-plan', /your 7-day plan/i],
    ['/meal-plan/meals/42', /planned meal #42/i],
    ['/grocery-list', /everything you need this week/i],
    ['/dashboard', /your week at a glance/i],
    ['/admin', /admin panel/i],
  ])('renders %s', (path, heading) => {
    renderRoute(path)
    expect(screen.getByRole('heading', { level: 1, name: heading })).toBeInTheDocument()
  })

  it('shows a 404 page for unknown routes', () => {
    renderRoute('/does-not-exist')
    expect(screen.getByText(/404 – page not found/i)).toBeInTheDocument()
  })

  it('navigates between pages using the main navigation', async () => {
    const user = userEvent.setup()
    const { router } = renderRoute('/')
    const nav = screen.getByRole('navigation', { name: 'Main' })
    await user.click(within(nav).getByRole('link', { name: 'Grocery List' }))
    expect(router.state.location.pathname).toBe('/grocery-list')
    expect(screen.getByRole('heading', { level: 1, name: /everything you need/i })).toBeInTheDocument()
  })

  it('keeps unfinished forms disabled and labels their status', () => {
    renderRoute('/login')
    expect(screen.getByRole('button', { name: 'Log in' })).toBeDisabled()
    expect(screen.getByRole('note')).toHaveTextContent(/in development/i)
  })
})

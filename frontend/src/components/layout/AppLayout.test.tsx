import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { renderRoute } from '../../test/renderRoute'

describe('AppLayout', () => {
  it('renders header, navigation, main content and footer', () => {
    renderRoute('/dashboard')
    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByRole('contentinfo')).toHaveTextContent(/not medical advice/i)
    expect(screen.getByRole('link', { name: /skip to content/i })).toHaveAttribute('href', '#main')
  })

  it('marks the active navigation link', () => {
    renderRoute('/meal-plan')
    const nav = screen.getByRole('navigation', { name: 'Main' })
    const active = nav.querySelector('a[aria-current="page"]')
    expect(active).toHaveTextContent('Meal Plan')
  })

  it('toggles the mobile menu', async () => {
    const user = userEvent.setup()
    renderRoute('/')
    const toggle = screen.getByRole('button', { name: /open menu/i })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    await user.click(toggle)
    expect(screen.getByRole('navigation', { name: 'Mobile' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /close menu/i })).toHaveAttribute('aria-expanded', 'true')
  })
})

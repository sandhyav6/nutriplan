import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { mockApi, session, USER } from '../test/mockApi'
import { renderRoute } from '../test/renderRoute'

describe('Login (UC-02)', () => {
  it('validates fields before calling the API', async () => {
    const calls = mockApi()
    renderRoute('/login')
    await userEvent.click(await screen.findByRole('button', { name: 'Log in' }))
    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument()
    expect(screen.getByText('Enter your password.')).toBeInTheDocument()
    expect(calls.some((c) => c.path === '/auth/login')).toBe(false)
  })

  it('shows the server error for wrong credentials', async () => {
    mockApi({
      'POST /auth/login': { status: 401, body: { error: { code: 'unauthorized', message: 'Invalid email or password.' } } },
    })
    renderRoute('/login')
    await userEvent.type(await screen.findByLabelText('Email'), 'asha@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'wrong-pass1')
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.')
  })

  it('logs in and follows a safe next parameter', async () => {
    const calls = mockApi({ 'POST /auth/login': session(USER), 'GET /grocery-lists/current': { status: 404, body: { error: { code: 'plan_not_found', message: 'none' } } } })
    const { router } = renderRoute('/login?next=%2Fgrocery-list')
    await userEvent.type(await screen.findByLabelText('Email'), 'asha@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'Secret123')
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/grocery-list'))
    const login = calls.find((c) => c.path === '/auth/login')
    expect(login?.body).toEqual({ email: 'asha@example.com', password: 'Secret123' })
    expect(login?.headers['X-CSRF-Token']).toBe('test-csrf')
  })

  it('ignores external redirect targets', async () => {
    mockApi({ 'POST /auth/login': session(USER), 'GET /dashboard': { status: 500, body: { error: { code: 'x', message: 'x' } } } })
    const { router } = renderRoute('/login?next=%2F%2Fevil.example')
    await userEvent.type(await screen.findByLabelText('Email'), 'asha@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'Secret123')
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/dashboard'))
  })
})

describe('Register (UC-01)', () => {
  it('checks password rules and confirmation', async () => {
    renderRoute('/register')
    await userEvent.type(await screen.findByLabelText('Full name'), 'Asha')
    await userEvent.type(screen.getByLabelText('Email'), 'asha@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'onlyletters')
    await userEvent.type(screen.getByLabelText('Confirm password'), 'different')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByText('Password must contain at least one number.')).toBeInTheDocument()
    expect(screen.getByText('Passwords do not match.')).toBeInTheDocument()
  })

  it('shows a duplicate email inline', async () => {
    mockApi({
      'POST /auth/register': {
        status: 409,
        body: { error: { code: 'conflict', message: 'An account with this email already exists.', details: { field: 'email' } } },
      },
    })
    renderRoute('/register')
    await userEvent.type(await screen.findByLabelText('Full name'), 'Asha')
    await userEvent.type(screen.getByLabelText('Email'), 'asha@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'Secret123')
    await userEvent.type(screen.getByLabelText('Confirm password'), 'Secret123')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByText('An account with this email already exists.')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toHaveAttribute('aria-invalid', 'true')
  })

  it('registers and continues to profile setup', async () => {
    mockApi({
      'POST /auth/register': { status: 201, body: session(USER, false) },
      'GET /profile': { status: 404, body: { error: { code: 'profile_not_found', message: 'none' } } },
      'GET /allergens': [],
      'GET /foods': [],
    })
    const { router } = renderRoute('/register')
    await userEvent.type(await screen.findByLabelText('Full name'), 'Asha')
    await userEvent.type(screen.getByLabelText('Email'), 'asha@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'Secret123')
    await userEvent.type(screen.getByLabelText('Confirm password'), 'Secret123')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/profile'))
    expect(await screen.findByText('Getting started')).toBeInTheDocument()
  })
})

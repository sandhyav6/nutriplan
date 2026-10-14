import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { PROFILE } from '../test/fixtures'
import { mockApi, USER } from '../test/mockApi'
import { renderRoute } from '../test/renderRoute'

const REFERENCE = {
  'GET /allergens': [
    { id: 1, name: 'Peanuts' },
    { id: 3, name: 'Dairy' },
  ],
  'GET /foods': [{ id: 46, name: 'Mushroom' }],
}
const NO_PROFILE = { status: 404, body: { error: { code: 'profile_not_found', message: 'none' } } }

describe('Profile (UC-04, UC-05)', () => {
  it('shows inline validation errors (REQ-4.1.4)', async () => {
    const calls = mockApi({ ...REFERENCE, 'GET /profile': NO_PROFILE }, { user: USER })
    renderRoute('/profile')
    await userEvent.click(await screen.findByRole('button', { name: 'Save profile' }, { timeout: 5000 }))
    expect(await screen.findByText('Age is required.')).toBeInTheDocument()
    expect(screen.getByText('Select a gender.')).toBeInTheDocument()
    expect(screen.getByText('Weekly budget is required.')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Weight (kg)'), '-60')
    await userEvent.click(screen.getByRole('button', { name: 'Save profile' }))
    expect(await screen.findByText('Weight must be between 25 and 300 kg.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'PUT')).toBe(false)
  }, 20_000)

  it('creates a profile with allergies and excluded foods and shows the nutrition target', async () => {
    const calls = mockApi(
      { ...REFERENCE, 'GET /profile': NO_PROFILE, 'PUT /profile': { status: 201, body: PROFILE } },
      { user: USER },
    )
    renderRoute('/profile')
    await userEvent.type(await screen.findByLabelText('Age'), '21')
    await userEvent.selectOptions(screen.getByLabelText('Gender'), 'female')
    await userEvent.type(screen.getByLabelText('Height (cm)'), '160')
    await userEvent.type(screen.getByLabelText('Weight (kg)'), '55')
    await userEvent.selectOptions(screen.getByLabelText('Activity level'), 'moderately_active')
    await userEvent.selectOptions(screen.getByLabelText('Dietary preference'), 'vegetarian')
    await userEvent.click(screen.getByLabelText('Peanuts'))
    await userEvent.type(screen.getByLabelText('Other foods you can’t eat'), 'mush')
    await userEvent.click(screen.getByRole('button', { name: 'Exclude Mushroom' }))
    await userEvent.selectOptions(screen.getByLabelText('Health goal'), 'maintenance')
    await userEvent.type(screen.getByLabelText('Weekly budget (₹)'), '1500')
    await userEvent.type(screen.getByLabelText('Cooking time per meal (min)'), '30')
    await userEvent.click(screen.getByRole('button', { name: 'Save profile' }))

    expect(await screen.findByText(/Profile saved/)).toBeInTheDocument()
    const put = calls.find((c) => c.method === 'PUT' && c.path === '/profile')
    expect(put?.body).toEqual({
      age: 21,
      gender: 'female',
      height_cm: 160,
      weight_kg: 55,
      activity_level: 'moderately_active',
      dietary_preference: 'vegetarian',
      health_goal: 'maintenance',
      weekly_budget_inr: 1500,
      max_cooking_time_min: 30,
      allergen_ids: [1],
      excluded_food_ids: [46],
    })
    expect(screen.getByText('21.5')).toBeInTheDocument()
    expect(screen.getAllByText('2,300').length).toBeGreaterThan(0)
  }, 20_000)

  it('loads an existing profile for editing (REQ-4.1.5)', async () => {
    mockApi({ ...REFERENCE, 'GET /profile': PROFILE }, { user: USER })
    renderRoute('/profile')
    expect(await screen.findByLabelText('Age')).toHaveValue(21)
    expect(screen.getByLabelText('Peanuts')).toBeChecked()
    expect(screen.getByRole('heading', { level: 1, name: 'Your profile' })).toBeInTheDocument()
  })

  it('maps server-side field errors onto the form', async () => {
    mockApi(
      {
        ...REFERENCE,
        'GET /profile': PROFILE,
        'PUT /profile': {
          status: 422,
          body: {
            error: {
              code: 'validation_error',
              message: 'The request contains invalid fields.',
              details: [{ location: ['body', 'age'], message: 'Input should be less than or equal to 100' }],
            },
          },
        },
      },
      { user: USER },
    )
    renderRoute('/profile')
    await userEvent.click(await screen.findByRole('button', { name: 'Save profile' }, { timeout: 5000 }))
    expect(await screen.findByText('Input should be less than or equal to 100')).toBeInTheDocument()
  })
})

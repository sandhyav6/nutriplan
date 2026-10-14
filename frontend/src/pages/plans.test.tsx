import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { DASHBOARD, GROCERY, MEAL_DETAIL, PLAN } from '../test/fixtures'
import { mockApi, USER } from '../test/mockApi'
import { renderRoute } from '../test/renderRoute'

const NO_PLAN = { status: 404, body: { error: { code: 'plan_not_found', message: 'No plan yet.' } } }

describe('Weekly meal plan (UC-06, UC-07)', () => {
  it('shows the empty state and generates a plan', async () => {
    const calls = mockApi(
      { 'GET /meal-plans/current': NO_PLAN, 'POST /meal-plans/generate': { status: 201, body: PLAN } },
      { user: USER },
    )
    renderRoute('/meal-plan')
    expect(await screen.findByText('No meal plan yet')).toBeInTheDocument()
    await userEvent.click(screen.getAllByRole('button', { name: 'Generate weekly plan' })[0])
    expect((await screen.findAllByText('Meal 1')).length).toBeGreaterThan(0)
    expect(calls.find((c) => c.path === '/meal-plans/generate')?.headers['X-CSRF-Token']).toBe('test-csrf')
  })

  it('renders 7 days x 4 slots with explanations and notes (REQ-4.2.1, REQ-4.2.8)', async () => {
    mockApi({ 'GET /meal-plans/current': PLAN }, { user: USER })
    renderRoute('/meal-plan')
    const table = await screen.findByRole('table', { name: 'Weekly meal plan' })
    expect(table.querySelectorAll('tbody tr')).toHaveLength(7)
    expect(table.querySelectorAll('thead th')).toHaveLength(5)
    expect(screen.getAllByText(/No safe dinner recipe/).length).toBeGreaterThan(0)
    expect(screen.getAllByText('Favourite').length).toBeGreaterThan(0)
    expect(screen.getByRole('meter', { name: 'Weekly cost against budget' })).toHaveAttribute('aria-valuenow', '810')
  })

  it('explains an infeasible budget', async () => {
    mockApi(
      {
        'GET /meal-plans/current': NO_PLAN,
        'POST /meal-plans/generate': {
          status: 422,
          body: {
            error: {
              code: 'budget_infeasible',
              message: 'A safe plan cannot fit your weekly budget of ₹100.',
              details: { minimum_weekly_cost_inr: '420.00' },
            },
          },
        },
      },
      { user: USER },
    )
    renderRoute('/meal-plan')
    await userEvent.click((await screen.findAllByRole('button', { name: 'Generate weekly plan' }))[0])
    expect(await screen.findByText(/cannot fit your weekly budget/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Adjust your budget' })).toHaveAttribute('href', '/profile')
  })
})

describe('Meal details (feedback & replacement)', () => {
  it('sends feedback (REQ-4.4.1)', async () => {
    const calls = mockApi(
      {
        'GET /meal-plans/current/meals/2': MEAL_DETAIL,
        'POST /feedback': { status: 201, body: { id: 1, planned_meal_id: 2, recipe_id: 102, feedback_type: 'like', score: 1, created_at: '' } },
      },
      { user: USER },
    )
    renderRoute('/meal-plan/meals/2')
    expect(await screen.findByText('Curd')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Like' }))
    expect(await screen.findByText(/Saved as “Like”/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Like' })).toHaveAttribute('aria-pressed', 'true')
    expect(calls.find((c) => c.path === '/feedback')?.body).toEqual({ planned_meal_id: 2, feedback_type: 'like' })
  })

  it('replaces a meal and avoids recipes already swapped out (REQ-4.5.1)', async () => {
    const replaced = { ...MEAL_DETAIL, meal: { ...MEAL_DETAIL.meal!, recipe_id: 999, name: 'New Lunch' } }
    const calls = mockApi(
      {
        'GET /meal-plans/current/meals/2': MEAL_DETAIL,
        'POST /meal-plans/current/meals/2/replace': { meal: replaced, total_calories_kcal: '15500', total_cost_inr: '800.00' },
      },
      { user: USER },
    )
    renderRoute('/meal-plan/meals/2')
    await userEvent.click(await screen.findByRole('button', { name: 'Replace meal' }))
    expect(await screen.findByRole('heading', { level: 1, name: 'New Lunch' })).toBeInTheDocument()
    expect(screen.getByText(/grocery list has been updated/)).toBeInTheDocument()
    expect(calls.find((c) => c.path.endsWith('/replace'))?.body).toEqual({ avoid_recipe_ids: [102] })
  })

  it('reports when no replacement exists (REQ-4.5.5)', async () => {
    mockApi(
      {
        'GET /meal-plans/current/meals/2': MEAL_DETAIL,
        'POST /meal-plans/current/meals/2/replace': {
          status: 409,
          body: { error: { code: 'no_replacement', message: 'No other lunch meal fits. Your current meal has been kept.' } },
        },
      },
      { user: USER },
    )
    renderRoute('/meal-plan/meals/2')
    await userEvent.click(await screen.findByRole('button', { name: 'Replace meal' }))
    expect(await screen.findByText(/current meal has been kept/)).toBeInTheDocument()
  })
})

describe('Grocery list (UC-09)', () => {
  it('shows grouped, readable quantities and the total against budget', async () => {
    mockApi({ 'GET /grocery-lists/current': GROCERY }, { user: USER })
    renderRoute('/grocery-list')
    expect(await screen.findByText('1.25 kg')).toBeInTheDocument()
    expect(screen.getByText('7 pieces')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Grains & Cereals' })).toBeInTheDocument()
    expect(screen.getByText('₹812')).toBeInTheDocument()
  })

  it('explains that a plan is needed first', async () => {
    mockApi({ 'GET /grocery-lists/current': NO_PLAN }, { user: USER })
    renderRoute('/grocery-list')
    expect(await screen.findByText('No grocery list yet')).toBeInTheDocument()
  })
})

describe('Dashboard (UC-12)', () => {
  it('summarises calories, spend, meal stats and favourites (REQ-4.6.x)', async () => {
    mockApi({ 'GET /dashboard': DASHBOARD }, { user: USER })
    renderRoute('/dashboard')
    expect(await screen.findByText('15,525 kcal')).toBeInTheDocument()
    expect(screen.getByText('₹812')).toBeInTheDocument()
    expect(screen.getByText('27 / 28')).toBeInTheDocument()
    expect(screen.getByText('Meal 1')).toBeInTheDocument()
    // The chart is lazy-loaded; its accessible table view mirrors the data.
    expect(await screen.findByRole('table', {}, { timeout: 8000 })).toHaveTextContent('Monday')
  }, 20_000)

  it('guides users without a profile', async () => {
    mockApi({ 'GET /dashboard': { ...DASHBOARD, has_plan: false, nutrition: null } }, { user: USER })
    renderRoute('/dashboard')
    expect(await screen.findByText('Start with your profile')).toBeInTheDocument()
  })
})

import { lazy, Suspense } from 'react'
import { Link } from 'react-router'

import { PageHeader } from '../components/layout/PageHeader'
import { Alert } from '../components/ui/Alert'
import { ButtonLink } from '../components/ui/Button'
import { Card, CardDescription, CardTitle } from '../components/ui/Card'
import { Meter } from '../components/ui/Meter'
import { EmptyState, LoadingState } from '../components/ui/StateViews'
import { useApi } from '../hooks/useApi'
import { useAuth } from '../hooks/useAuth'
import { FEEDBACK_LABELS, formatINR, formatKcal, SLOT_LABELS, SLOTS } from '../lib/format'
import type { Dashboard, FeedbackType } from '../types/api'

const DailyCaloriesChart = lazy(() =>
  import('../features/dashboard/DailyCaloriesChart').then((m) => ({ default: m.DailyCaloriesChart })),
)

const FEEDBACK_KEYS: (FeedbackType | 'none')[] = ['favourite', 'like', 'skip', 'dislike', 'none']

export function DashboardPage() {
  const { state } = useAuth()
  const dash = useApi<Dashboard>('/dashboard')
  const name = state.status === 'authenticated' ? state.user.full_name.split(' ')[0] : ''

  return (
    <>
      <PageHeader
        eyebrow="Dashboard"
        title={name ? `Hello, ${name}` : 'Your week at a glance'}
        description="Weekly calories, estimated spending, meal statistics and your favourite meals."
      />
      {dash.status === 'loading' && <LoadingState label="Loading your dashboard…" />}
      {dash.status === 'error' && <Alert tone="error">{dash.error.message}</Alert>}
      {dash.status === 'success' && <DashboardView data={dash.data} />}
    </>
  )
}

function DashboardView({ data }: { data: Dashboard }) {
  if (!data.nutrition) {
    return (
      <EmptyState title="Start with your profile" action={<ButtonLink to="/profile">Create profile</ButtonLink>}>
        Tell NutriPlan about your diet, goal, budget and cooking time to get your first plan.
      </EmptyState>
    )
  }
  if (!data.has_plan) {
    return (
      <EmptyState title="No meal plan yet" action={<ButtonLink to="/meal-plan">Generate a plan</ButtonLink>}>
        Your daily target is {formatKcal(data.nutrition.daily_calories_kcal)} and{' '}
        {data.nutrition.daily_protein_g} g protein. Generate a plan to see your weekly summary.
      </EmptyState>
    )
  }

  const spend = Number(data.estimated_spend_inr)
  const budget = Number(data.weekly_budget_inr ?? 0)
  const weeklyTarget = data.nutrition.daily_calories_kcal * 7
  const plannedMeals = Object.values(data.meals_by_slot).reduce((a, b) => a + (b ?? 0), 0)

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-sm font-medium text-ink-muted">Weekly calories</p>
          <p className="mt-2 text-2xl font-bold text-ink">{formatKcal(data.total_calories_kcal)}</p>
          <p className="mt-1 text-xs text-ink-muted">Target {formatKcal(weeklyTarget)}</p>
        </Card>
        <Card>
          <p className="text-sm font-medium text-ink-muted">Daily average</p>
          <p className="mt-2 text-2xl font-bold text-ink">{formatKcal(data.average_daily_calories_kcal)}</p>
          <p className="mt-1 text-xs text-ink-muted">
            {data.average_daily_protein_g} g protein · target {data.nutrition.daily_protein_g} g
          </p>
        </Card>
        <Card>
          <p className="text-sm font-medium text-ink-muted">Estimated spend</p>
          <p className="mt-2 text-2xl font-bold text-ink">{formatINR(spend)}</p>
          <div className="mt-2">
            <Meter value={spend} max={budget} label="Estimated spend against weekly budget" />
          </div>
          <p className="mt-1 text-xs text-ink-muted">
            {spend <= budget ? `${formatINR(budget - spend)} under` : `${formatINR(spend - budget)} over`} your{' '}
            {formatINR(budget)} budget
          </p>
        </Card>
        <Card>
          <p className="text-sm font-medium text-ink-muted">Meals planned</p>
          <p className="mt-2 text-2xl font-bold text-ink">{plannedMeals} / 28</p>
          <p className="mt-1 text-xs text-ink-muted">
            {data.unavailable_slots ? `${data.unavailable_slots} slot(s) could not be filled` : 'Every slot filled'}
          </p>
        </Card>
      </div>

      <Card>
        <CardTitle>Calories per day</CardTitle>
        <CardDescription>Planned calories for each day of this week, compared with your daily target.</CardDescription>
        <div className="mt-4">
          <Suspense fallback={<LoadingState label="Loading chart…" />}>
            <DailyCaloriesChart days={data.days} target={data.nutrition.daily_calories_kcal} />
          </Suspense>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <CardTitle>Meals by category</CardTitle>
          <ul className="mt-4 space-y-3">
            {SLOTS.map((slot) => {
              const count = data.meals_by_slot[slot] ?? 0
              return (
                <li key={slot}>
                  <div className="flex justify-between text-sm">
                    <span className="text-ink">{SLOT_LABELS[slot]}</span>
                    <span className="font-semibold text-ink">{count} / 7</span>
                  </div>
                  <div className="mt-1">
                    <Meter value={count} max={7} label={`${SLOT_LABELS[slot]} meals planned`} />
                  </div>
                </li>
              )
            })}
          </ul>
        </Card>

        <Card>
          <CardTitle>Your feedback this week</CardTitle>
          <dl className="mt-4 space-y-2 text-sm">
            {FEEDBACK_KEYS.map((key) => (
              <div key={key} className="flex justify-between">
                <dt className="text-ink">{key === 'none' ? 'No feedback yet' : FEEDBACK_LABELS[key]}</dt>
                <dd className="font-semibold text-ink">{data.feedback_on_plan[key] ?? 0}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-4 text-xs text-ink-muted">{data.total_feedback_events} feedback events in total.</p>
        </Card>

        <Card>
          <CardTitle>Favourite meals</CardTitle>
          {data.favourites.length ? (
            <ul className="mt-4 space-y-2 text-sm">
              {data.favourites.map((f) => (
                <li key={f.recipe_id} className="flex justify-between gap-3">
                  <span className="text-ink">{f.name}</span>
                  <span className="text-ink-muted">{SLOT_LABELS[f.slot]}</span>
                </li>
              ))}
            </ul>
          ) : (
            <CardDescription>
              Mark meals as Favourite on the{' '}
              <Link to="/meal-plan" className="font-semibold text-brand-700 underline">
                meal plan
              </Link>{' '}
              and similar meals will be recommended more often.
            </CardDescription>
          )}
        </Card>
      </div>
    </div>
  )
}

import { Fragment, useState } from 'react'
import { Link } from 'react-router'

import { PageHeader } from '../components/layout/PageHeader'
import { Alert } from '../components/ui/Alert'
import { Button, ButtonLink } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Meter } from '../components/ui/Meter'
import { EmptyState, LoadingState } from '../components/ui/StateViews'
import { MealCard } from '../features/meal-plan/MealCard'
import { useApi } from '../hooks/useApi'
import { apiClient, ApiError } from '../lib/apiClient'
import { DAYS, formatDate, formatINR, formatKcal, SLOT_LABELS, SLOTS } from '../lib/format'
import type { MealPlan } from '../types/api'

export function MealPlanPage() {
  const plan = useApi<MealPlan>('/meal-plans/current')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  async function generate() {
    setGenerating(true)
    setError(null)
    try {
      plan.setData(await apiClient.post<MealPlan>('/meal-plans/generate'))
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, 'unknown', 'Could not generate a plan.'))
    } finally {
      setGenerating(false)
    }
  }

  const hasPlan = plan.status === 'success'
  const generateButton = (
    <Button onClick={generate} disabled={generating}>
      {generating ? 'Generating…' : hasPlan ? 'Regenerate plan' : 'Generate weekly plan'}
    </Button>
  )

  return (
    <>
      <PageHeader
        eyebrow="Weekly meal plan"
        title="Your 7-day plan"
        description="Breakfast, lunch, dinner and a snack for every day, chosen by the rule engine to fit your diet, allergies, budget and cooking time."
        actions={
          <>
            {hasPlan && (
              <ButtonLink to="/grocery-list" variant="secondary">
                Grocery list
              </ButtonLink>
            )}
            {generateButton}
          </>
        }
      />

      {error && (
        <Alert tone="error" title="The plan could not be generated" className="mb-6">
          {error.message}{' '}
          {error.code === 'profile_required' && (
            <Link to="/profile" className="font-semibold underline">
              Complete your profile
            </Link>
          )}
          {error.code === 'budget_infeasible' && (
            <Link to="/profile" className="font-semibold underline">
              Adjust your budget
            </Link>
          )}
        </Alert>
      )}

      {plan.status === 'loading' && <LoadingState label="Loading your plan…" />}

      {plan.status === 'error' &&
        (plan.error.status === 404 ? (
          <EmptyState title="No meal plan yet" action={generateButton}>
            Generate a plan to get seven days of meals that fit your profile, plus a combined grocery
            list for the week.
          </EmptyState>
        ) : (
          <Alert tone="error">{plan.error.message}</Alert>
        ))}

      {hasPlan && <PlanView plan={plan.data} />}
    </>
  )
}

function PlanView({ plan }: { plan: MealPlan }) {
  const avgCalories = Number(plan.total_calories_kcal) / 7
  const cost = Number(plan.total_cost_inr)
  const budget = Number(plan.weekly_budget_inr)

  return (
    <div className="space-y-6">
      {plan.profile_changed_since_generation && (
        <Alert tone="warning" title="Your profile has changed">
          This plan was generated before your latest profile update. Regenerate it to apply the
          new settings.
        </Alert>
      )}
      {plan.notes.map((note) => (
        <Alert key={note.message} tone="warning">
          {note.message}
        </Alert>
      ))}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm font-medium text-ink-muted">Week of</p>
          <p className="mt-1 text-xl font-bold text-ink">
            {formatDate(plan.week_start_date, { day: 'numeric', month: 'long', year: 'numeric' })}
          </p>
        </Card>
        <Card>
          <p className="text-sm font-medium text-ink-muted">Average per day</p>
          <p className="mt-1 text-xl font-bold text-ink">{formatKcal(avgCalories)}</p>
          <p className="text-xs text-ink-muted">Target {formatKcal(plan.nutrition.daily_calories_kcal)}</p>
        </Card>
        <Card>
          <p className="text-sm font-medium text-ink-muted">Estimated cost</p>
          <p className="mt-1 text-xl font-bold text-ink">
            {formatINR(cost)} <span className="text-sm font-normal text-ink-muted">of {formatINR(budget)}</span>
          </p>
          <div className="mt-2">
            <Meter value={cost} max={budget} label="Weekly cost against budget" />
          </div>
        </Card>
      </div>

      {/* Desktop: days as rows, slots as columns */}
      <div className="hidden overflow-x-auto rounded-2xl border border-line bg-surface lg:block">
        <table className="w-full border-collapse text-left text-sm">
          <caption className="sr-only">Weekly meal plan</caption>
          <thead>
            <tr className="border-b border-line bg-surface-muted/70">
              <th scope="col" className="w-32 px-3 py-3 font-semibold">
                Day
              </th>
              {SLOTS.map((slot) => (
                <th key={slot} scope="col" className="px-3 py-3 font-semibold">
                  {SLOT_LABELS[slot]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {DAYS.map((day, d) => {
              const totals = plan.days[d]
              return (
                <tr key={day} className="border-b border-line align-top last:border-0">
                  <th scope="row" className="px-3 py-3 font-medium">
                    <span className="block text-ink">{day}</span>
                    <span className="block text-xs font-normal text-ink-muted">{formatDate(totals.date)}</span>
                    <span className="mt-1 block text-xs font-normal text-ink-muted">
                      {formatKcal(totals.calories_kcal)}
                    </span>
                  </th>
                  {SLOTS.map((slot) => {
                    const planned = plan.meals.find((m) => m.day_of_week === d && m.slot === slot)
                    return (
                      <td key={slot} className="p-2">
                        {planned && <MealCard planned={planned} />}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile / tablet: one card per day */}
      <div className="space-y-4 lg:hidden">
        {DAYS.map((day, d) => (
          <Card key={day} className="p-4">
            <h2 className="flex items-baseline justify-between font-semibold text-ink">
              {day}
              <span className="text-xs font-normal text-ink-muted">
                {formatDate(plan.days[d].date)} · {formatKcal(plan.days[d].calories_kcal)}
              </span>
            </h2>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {SLOTS.map((slot) => {
                const planned = plan.meals.find((m) => m.day_of_week === d && m.slot === slot)
                return (
                  <Fragment key={slot}>
                    {planned && (
                      <div>
                        <p className="mb-1 text-xs font-semibold tracking-wide text-ink-muted uppercase">
                          {SLOT_LABELS[slot]}
                        </p>
                        <MealCard planned={planned} />
                      </div>
                    )}
                  </Fragment>
                )
              })}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}

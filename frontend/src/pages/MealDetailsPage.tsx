import { useState } from 'react'
import { useParams } from 'react-router'

import { PageHeader } from '../components/layout/PageHeader'
import { Alert } from '../components/ui/Alert'
import { Button, ButtonLink } from '../components/ui/Button'
import { Card, CardDescription, CardTitle } from '../components/ui/Card'
import { LoadingState } from '../components/ui/StateViews'
import { useApi } from '../hooks/useApi'
import { apiClient, errorMessage } from '../lib/apiClient'
import { cn } from '../lib/cn'
import {
  DAYS,
  DIET_LABELS,
  FEEDBACK_LABELS,
  formatDate,
  formatINR,
  formatQuantity,
  SLOT_LABELS,
} from '../lib/format'
import type { FeedbackType, MealDetail, ReplaceResult } from '../types/api'

const FEEDBACK_ORDER: FeedbackType[] = ['favourite', 'like', 'skip', 'dislike']
const FEEDBACK_HELP: Record<FeedbackType, string> = {
  favourite: 'Recommend this and similar meals more often (+3)',
  like: 'Recommend this meal more often (+1)',
  skip: 'Recommend this meal a little less (−1)',
  dislike: 'Recommend this meal much less (−3)',
}

export function MealDetailsPage() {
  const { mealId } = useParams()
  const detail = useApi<MealDetail>(`/meal-plans/current/meals/${mealId}`)
  const [busy, setBusy] = useState<string | null>(null)
  // Recipes already swapped out of this slot, so repeated replacements keep offering new meals.
  const [swappedOut, setSwappedOut] = useState<number[]>([])
  const [status, setStatus] = useState<{ tone: 'success' | 'error' | 'warning'; text: string } | null>(null)

  if (detail.status === 'loading') return <LoadingState label="Loading meal…" />
  if (detail.status === 'error') {
    return (
      <div className="space-y-4">
        <Alert tone="error">{detail.error.message}</Alert>
        <ButtonLink to="/meal-plan" variant="secondary">
          Back to meal plan
        </ButtonLink>
      </div>
    )
  }

  const data = detail.data
  const meal = data.meal

  async function sendFeedback(type: FeedbackType) {
    setBusy(type)
    setStatus(null)
    try {
      await apiClient.post('/feedback', { planned_meal_id: data.id, feedback_type: type })
      detail.setData({ ...data, feedback: type })
      setStatus({ tone: 'success', text: `Saved as “${FEEDBACK_LABELS[type]}”. Future plans will take this into account.` })
    } catch (error) {
      setStatus({ tone: 'error', text: errorMessage(error) })
    } finally {
      setBusy(null)
    }
  }

  async function replace() {
    setBusy('replace')
    setStatus(null)
    const previous = meal?.name
    try {
      const avoid = meal ? [...swappedOut, meal.recipe_id] : swappedOut
      const result = await apiClient.post<ReplaceResult>(`/meal-plans/current/meals/${data.id}/replace`, {
        avoid_recipe_ids: avoid,
      })
      setSwappedOut(avoid)
      detail.setData(result.meal)
      setStatus({
        tone: 'success',
        text: `${previous ?? 'The meal'} was replaced with ${result.meal.meal?.name}. Your grocery list has been updated. New weekly cost: ${formatINR(result.total_cost_inr)}.`,
      })
    } catch (error) {
      setStatus({ tone: 'warning', text: errorMessage(error) })
    } finally {
      setBusy(null)
    }
  }

  const when = `${DAYS[data.day_of_week]}, ${formatDate(data.date)} · ${SLOT_LABELS[data.slot]}`

  return (
    <>
      <PageHeader
        eyebrow={when}
        title={meal?.name ?? `No ${SLOT_LABELS[data.slot].toLowerCase()} planned`}
        description={meal ? `${DIET_LABELS[meal.diet_type]} · ready in ${meal.prep_time_min} minutes` : data.unavailable_reason ?? undefined}
        actions={
          <ButtonLink to="/meal-plan" variant="secondary">
            Back to meal plan
          </ButtonLink>
        }
      />

      {status && (
        <Alert tone={status.tone} className="mb-6">
          {status.text}
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="space-y-6">
          {meal && (
            <Card>
              <CardTitle>Nutrition for your portion</CardTitle>
              <CardDescription>
                {Number(meal.servings) === 1
                  ? 'One standard serving.'
                  : `${Number(meal.servings)} servings – portion sized to your calorie target.`}{' '}
                Values are estimates, not medical advice.
              </CardDescription>
              <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                {[
                  ['Calories', `${Math.round(Number(meal.calories_kcal))} kcal`],
                  ['Protein', `${meal.protein_g} g`],
                  ['Carbohydrates', `${meal.carbs_g} g`],
                  ['Fat', `${meal.fat_g} g`],
                  ['Fibre', data.fibre_g ? `${data.fibre_g} g` : '—'],
                  ['Sugar', data.sugar_g ? `${data.sugar_g} g` : '—'],
                  ['Estimated cost', formatINR(meal.cost_inr, true)],
                  ['Prep time', `${meal.prep_time_min} min`],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-xl bg-surface-muted/70 p-3">
                    <dt className="text-xs font-medium text-ink-muted">{label}</dt>
                    <dd className="mt-1 font-semibold text-ink">{value}</dd>
                  </div>
                ))}
              </dl>
            </Card>
          )}

          {meal && (
            <Card>
              <CardTitle>Ingredients</CardTitle>
              <ul className="mt-3 divide-y divide-line">
                {data.ingredients.map((i) => (
                  <li key={i.food_id} className="flex justify-between gap-4 py-2 text-sm">
                    <span className="text-ink">{i.name}</span>
                    <span className="text-ink-muted">{formatQuantity(i.quantity, i.unit)}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-ink-muted">
                Contains: {data.allergens.length ? data.allergens.join(', ') : 'none of the tracked allergens'}
              </p>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          {meal && (
            <Card>
              <CardTitle>Your feedback</CardTitle>
              <CardDescription>Feedback adjusts how often this meal is recommended.</CardDescription>
              <div className="mt-4 grid grid-cols-2 gap-2" role="group" aria-label="Meal feedback">
                {FEEDBACK_ORDER.map((type) => (
                  <button
                    key={type}
                    type="button"
                    title={FEEDBACK_HELP[type]}
                    aria-label={FEEDBACK_LABELS[type]}
                    aria-pressed={data.feedback === type}
                    disabled={busy !== null}
                    onClick={() => sendFeedback(type)}
                    className={cn(
                      'rounded-lg border px-3 py-2 text-sm font-semibold transition-colors disabled:opacity-60',
                      data.feedback === type
                        ? 'border-brand-600 bg-brand-600 text-white'
                        : 'border-line bg-surface text-ink hover:bg-surface-muted',
                    )}
                  >
                    {FEEDBACK_LABELS[type]}
                  </button>
                ))}
              </div>
            </Card>
          )}
          <Card>
            <CardTitle>Replace this meal</CardTitle>
            <CardDescription>
              Swap in another {SLOT_LABELS[data.slot].toLowerCase()} with the same diet and allergy
              rules, similar calories (±20%) and without going over your weekly budget.
            </CardDescription>
            <Button className="mt-4 w-full" onClick={replace} disabled={busy !== null}>
              {busy === 'replace' ? 'Finding a replacement…' : 'Replace meal'}
            </Button>
          </Card>
        </div>
      </div>
    </>
  )
}

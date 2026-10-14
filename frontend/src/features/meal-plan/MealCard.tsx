import { Link } from 'react-router'

import { cn } from '../../lib/cn'
import { FEEDBACK_LABELS, formatINR, SLOT_LABELS } from '../../lib/format'
import type { PlannedMeal } from '../../types/api'

const FEEDBACK_STYLE = {
  favourite: 'bg-brand-600 text-white',
  like: 'bg-brand-100 text-brand-800',
  skip: 'bg-surface-muted text-ink-muted',
  dislike: 'bg-danger-50 text-danger-700',
} as const

export function MealCard({ planned }: { planned: PlannedMeal }) {
  if (!planned.meal) {
    return (
      <div className="h-full rounded-xl border border-dashed border-caution-200 bg-caution-50 p-3 text-xs leading-relaxed text-caution-800">
        <p className="font-semibold">No {SLOT_LABELS[planned.slot].toLowerCase()} planned</p>
        <p className="mt-1">{planned.unavailable_reason}</p>
      </div>
    )
  }
  const m = planned.meal
  return (
    <Link
      to={`/meal-plan/meals/${planned.id}`}
      className="group flex h-full flex-col rounded-xl border border-line bg-surface p-3 transition hover:border-brand-500 hover:shadow-sm"
    >
      <span className="text-sm leading-snug font-semibold text-ink group-hover:text-brand-700">{m.name}</span>
      <span className="mt-1 text-xs text-ink-muted">
        {Math.round(Number(m.calories_kcal))} kcal · {Math.round(Number(m.protein_g))} g protein
      </span>
      <span className="mt-auto flex flex-wrap items-center gap-x-2 gap-y-1 pt-2 text-xs text-ink-muted">
        <span>{formatINR(m.cost_inr)}</span>
        <span aria-hidden="true">·</span>
        <span>{m.prep_time_min} min</span>
        {Number(m.servings) !== 1 && (
          <>
            <span aria-hidden="true">·</span>
            <span>{Number(m.servings)}× serving</span>
          </>
        )}
        {planned.feedback && (
          <span className={cn('ml-auto rounded-full px-2 py-0.5 font-semibold', FEEDBACK_STYLE[planned.feedback])}>
            {FEEDBACK_LABELS[planned.feedback]}
          </span>
        )}
      </span>
    </Link>
  )
}

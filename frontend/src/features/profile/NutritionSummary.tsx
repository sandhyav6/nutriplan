import { Card, CardDescription, CardTitle } from '../../components/ui/Card'
import type { NutritionTarget } from '../../types/api'

export function NutritionSummary({ nutrition }: { nutrition: NutritionTarget | null }) {
  return (
    <Card className="h-fit">
      <CardTitle>Your nutrition profile</CardTitle>
      {nutrition ? (
        <>
          <dl className="mt-4 grid grid-cols-2 gap-4">
            <div>
              <dt className="text-xs font-medium text-ink-muted uppercase">BMI</dt>
              <dd className="mt-1 text-2xl font-bold text-ink">{nutrition.bmi}</dd>
              <dd className="text-sm text-ink-muted capitalize">{nutrition.bmi_category}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-ink-muted uppercase">Daily calories</dt>
              <dd className="mt-1 text-2xl font-bold text-ink">
                {nutrition.daily_calories_kcal.toLocaleString('en-IN')}
              </dd>
              <dd className="text-sm text-ink-muted">kcal / day</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-ink-muted uppercase">Protein</dt>
              <dd className="mt-1 text-2xl font-bold text-ink">{nutrition.daily_protein_g} g</dd>
              <dd className="text-sm text-ink-muted">per day</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-ink-muted uppercase">Activity baseline</dt>
              <dd className="mt-1 text-2xl font-bold text-ink">
                {nutrition.baseline_calories_kcal.toLocaleString('en-IN')}
              </dd>
              <dd className="text-sm text-ink-muted">kcal before your goal</dd>
            </div>
          </dl>
          {nutrition.prioritise_weight_loss_meals && (
            <p className="mt-4 rounded-lg bg-brand-50 px-3 py-2 text-sm text-brand-800">
              Your BMI is above 25, so lighter, protein-rich meals get extra priority.
            </p>
          )}
          <p className="mt-4 text-xs leading-relaxed text-ink-muted">
            BMI = weight ÷ height². Calories start from your activity level and are adjusted for
            your goal. These are estimates, not medical advice.
          </p>
        </>
      ) : (
        <CardDescription>
          Save your profile to see your BMI, daily calorie target and protein target. They are
          calculated before any meal is recommended.
        </CardDescription>
      )}
    </Card>
  )
}

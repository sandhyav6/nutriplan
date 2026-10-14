import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { DevelopmentNotice } from '../components/ui/DevelopmentNotice'
import { DAYS, MEAL_SLOTS } from '../features/meal-plan/constants'

export function MealPlanPage() {
  return (
    <>
      <PageHeader
        eyebrow="Weekly meal plan"
        title="Your 7-day plan"
        description="Breakfast, lunch, dinner and a snack for every day of the week, selected by the rule engine."
        actions={<Button disabled>Generate weekly plan</Button>}
      />
      <div className="space-y-6">
        <DevelopmentNotice milestone="planner">
          Plan generation is not implemented yet. The grid below is an empty layout preview – it
          contains no recommendations.
        </DevelopmentNotice>

        <div className="overflow-x-auto rounded-2xl border border-line bg-surface">
          <table className="w-full min-w-[720px] border-collapse text-left text-sm">
            <caption className="sr-only">Weekly meal plan layout (empty)</caption>
            <thead>
              <tr className="border-b border-line bg-surface-muted/70">
                <th scope="col" className="px-4 py-3 font-semibold text-ink">
                  Day
                </th>
                {MEAL_SLOTS.map((slot) => (
                  <th key={slot} scope="col" className="px-4 py-3 font-semibold text-ink">
                    {slot}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {DAYS.map((day) => (
                <tr key={day} className="border-b border-line last:border-0">
                  <th scope="row" className="px-4 py-3 font-medium text-ink">
                    {day}
                  </th>
                  {MEAL_SLOTS.map((slot) => (
                    <td key={slot} className="px-4 py-3">
                      <div className="rounded-lg border border-dashed border-line px-3 py-4 text-center text-xs text-ink-muted">
                        No meal yet
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}

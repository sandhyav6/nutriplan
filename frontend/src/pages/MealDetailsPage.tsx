import { useParams } from 'react-router'

import { PageHeader } from '../components/layout/PageHeader'
import { Button, ButtonLink } from '../components/ui/Button'
import { Card, CardDescription, CardTitle } from '../components/ui/Card'
import { DevelopmentNotice } from '../components/ui/DevelopmentNotice'
import { EmptyState } from '../components/ui/StateViews'

const FEEDBACK_ACTIONS = ['Like', 'Dislike', 'Skip', 'Favourite'] as const

export function MealDetailsPage() {
  const { mealId } = useParams()

  return (
    <>
      <PageHeader
        eyebrow="Meal details"
        title={`Planned meal #${mealId ?? ''}`}
        description="Nutrition, ingredients, estimated cost and feedback for a single meal in your plan."
        actions={
          <ButtonLink to="/meal-plan" variant="secondary">
            Back to meal plan
          </ButtonLink>
        }
      />
      <div className="space-y-6">
        <DevelopmentNotice milestone="feedback">
          Meal details are shown once plans exist (M3). Feedback and the Replace Meal action
          (REQ-4.4.1, REQ-4.5.1) are implemented in M5; the controls below are disabled.
        </DevelopmentNotice>

        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <Card>
            <CardTitle>Nutrition and ingredients</CardTitle>
            <EmptyState title="No meal data" className="mt-4">
              There is no meal with this id yet because plan generation has not been built.
            </EmptyState>
          </Card>
          <Card className="h-fit">
            <CardTitle>Your feedback</CardTitle>
            <CardDescription>Feedback adjusts how often this meal is recommended in future plans.</CardDescription>
            <div className="mt-4 grid grid-cols-2 gap-2">
              {FEEDBACK_ACTIONS.map((label) => (
                <Button key={label} variant="secondary" disabled>
                  {label}
                </Button>
              ))}
            </div>
            <Button className="mt-4 w-full" disabled>
              Replace meal
            </Button>
          </Card>
        </div>
      </div>
    </>
  )
}

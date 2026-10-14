import { PageHeader } from '../components/layout/PageHeader'
import { ButtonLink } from '../components/ui/Button'
import { Card, CardDescription, CardTitle } from '../components/ui/Card'
import { DevelopmentNotice } from '../components/ui/DevelopmentNotice'
import { EmptyState } from '../components/ui/StateViews'

export function GroceryListPage() {
  return (
    <>
      <PageHeader
        eyebrow="Grocery list"
        title="Everything you need this week"
        description="Ingredients from all 7 days are combined, duplicates are removed and quantities are added together (e.g. 200 g + 300 g = 500 g)."
      />
      <div className="space-y-6">
        <DevelopmentNotice milestone="grocery">
          Grocery aggregation is not implemented yet, so no list or cost estimate is shown.
        </DevelopmentNotice>

        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <EmptyState
            title="No grocery list yet"
            action={
              <ButtonLink to="/meal-plan" variant="secondary">
                Go to meal plan
              </ButtonLink>
            }
          >
            A grocery list is generated automatically from your weekly meal plan and refreshed
            whenever you replace a meal.
          </EmptyState>
          <Card className="h-fit">
            <CardTitle>Estimated spend</CardTitle>
            <CardDescription>
              The total estimated cost will be compared with your weekly budget (₹) here.
            </CardDescription>
          </Card>
        </div>
      </div>
    </>
  )
}

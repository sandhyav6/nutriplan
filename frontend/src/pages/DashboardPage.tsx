import { PageHeader } from '../components/layout/PageHeader'
import { Card } from '../components/ui/Card'
import { DevelopmentNotice } from '../components/ui/DevelopmentNotice'
import { EmptyState } from '../components/ui/StateViews'

const METRICS = [
  { label: 'Weekly calories', hint: 'Total planned kcal vs. your target' },
  { label: 'Estimated spend', hint: 'Grocery cost vs. weekly budget (₹)' },
  { label: 'Meals planned', hint: 'Counts by category' },
  { label: 'Favourite meals', hint: 'Meals you marked as favourite' },
] as const

export function DashboardPage() {
  return (
    <>
      <PageHeader
        eyebrow="Dashboard"
        title="Your week at a glance"
        description="Weekly calories, estimated spending, meal statistics and favourite meals."
      />
      <div className="space-y-6">
        <DevelopmentNotice milestone="dashboard">
          The dashboard (REQ-4.6.1 – REQ-4.6.4) is built once plans, grocery lists and feedback
          exist. No statistics are shown because there is no user data yet.
        </DevelopmentNotice>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {METRICS.map((metric) => (
            <Card key={metric.label}>
              <p className="text-sm font-medium text-ink-muted">{metric.label}</p>
              <p className="mt-2 text-2xl font-bold text-ink" aria-label={`${metric.label}: no data`}>
                —
              </p>
              <p className="mt-1 text-xs text-ink-muted">{metric.hint}</p>
            </Card>
          ))}
        </div>

        <EmptyState title="No charts yet">
          Daily calorie and spending charts will appear here after your first meal plan is
          generated.
        </EmptyState>
      </div>
    </>
  )
}

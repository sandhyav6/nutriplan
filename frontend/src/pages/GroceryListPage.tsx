import { PageHeader } from '../components/layout/PageHeader'
import { Alert } from '../components/ui/Alert'
import { Button, ButtonLink } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Meter } from '../components/ui/Meter'
import { EmptyState, LoadingState } from '../components/ui/StateViews'
import { useApi } from '../hooks/useApi'
import { formatDate, formatINR } from '../lib/format'
import type { GroceryList } from '../types/api'

export function GroceryListPage() {
  const list = useApi<GroceryList>('/grocery-lists/current')

  return (
    <>
      <PageHeader
        eyebrow="Grocery list"
        title="Everything you need this week"
        description="Ingredients from all 7 days are combined, duplicates are removed and quantities are added together. The list updates automatically when you replace a meal."
        actions={
          list.status === 'success' && (
            <Button variant="secondary" onClick={() => window.print()}>
              Print list
            </Button>
          )
        }
      />

      {list.status === 'loading' && <LoadingState label="Loading grocery list…" />}
      {list.status === 'error' &&
        (list.error.status === 404 ? (
          <EmptyState title="No grocery list yet" action={<ButtonLink to="/meal-plan">Go to meal plan</ButtonLink>}>
            Your grocery list is created automatically when you generate a weekly meal plan.
          </EmptyState>
        ) : (
          <Alert tone="error">{list.error.message}</Alert>
        ))}

      {list.status === 'success' && <GroceryView list={list.data} />}
    </>
  )
}

function GroceryView({ list }: { list: GroceryList }) {
  const total = Number(list.total_estimated_cost_inr)
  const budget = Number(list.weekly_budget_inr)
  return (
    <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
      <div className="space-y-4">
        {list.groups.map((group) => (
          <Card key={group.food_group} className="p-0 sm:p-0">
            <div className="flex items-baseline justify-between border-b border-line px-5 py-3">
              <h2 className="font-semibold text-ink">{group.food_group}</h2>
              <span className="text-sm text-ink-muted">{formatINR(group.subtotal_inr)}</span>
            </div>
            <table className="w-full text-sm">
              <caption className="sr-only">{group.food_group}</caption>
              <thead className="sr-only">
                <tr>
                  <th scope="col">Item</th>
                  <th scope="col">Quantity</th>
                  <th scope="col">Estimated cost</th>
                </tr>
              </thead>
              <tbody>
                {group.items.map((item) => (
                  <tr key={item.food_id} className="border-b border-line last:border-0">
                    <td className="px-5 py-2.5 text-ink">
                      <label className="flex items-center gap-3">
                        <input type="checkbox" className="accent-brand-600 print:hidden" aria-label={`Bought ${item.name}`} />
                        {item.name}
                      </label>
                    </td>
                    <td className="px-3 py-2.5 text-right whitespace-nowrap text-ink">{item.display_quantity}</td>
                    <td className="px-5 py-2.5 text-right whitespace-nowrap text-ink-muted">
                      {formatINR(item.estimated_cost_inr, true)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        ))}
      </div>

      <Card className="h-fit lg:sticky lg:top-24">
        <p className="text-sm font-medium text-ink-muted">Week of {formatDate(list.week_start_date, { day: 'numeric', month: 'long' })}</p>
        <p className="mt-3 text-sm font-medium text-ink-muted">Estimated total</p>
        <p className="text-3xl font-bold text-ink">{formatINR(total)}</p>
        <p className="mt-1 text-sm text-ink-muted">Weekly budget {formatINR(budget)}</p>
        <div className="mt-3">
          <Meter value={total} max={budget} label="Grocery cost against weekly budget" />
        </div>
        <p className="mt-3 text-sm text-ink-muted">{list.item_count} different items</p>
        <p className="mt-4 text-xs leading-relaxed text-ink-muted">
          Costs are estimates for the exact quantities your meals use, based on catalogue prices.
          Shop pack sizes may differ.
        </p>
      </Card>
    </div>
  )
}

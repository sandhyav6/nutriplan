import { useState } from 'react'

import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { Card, CardDescription, CardTitle } from '../components/ui/Card'
import { DevelopmentNotice } from '../components/ui/DevelopmentNotice'
import { EmptyState } from '../components/ui/StateViews'
import { cn } from '../lib/cn'

const SECTIONS = [
  {
    id: 'foods',
    label: 'Foods',
    requirement: 'REQ-4.7.2',
    text: 'Ingredients with their unit, price in ₹, diet type and allergens.',
  },
  {
    id: 'recipes',
    label: 'Recipes',
    requirement: 'REQ-4.7.3',
    text: 'Recipes with ingredient lists, quantities, preparation time and meal category.',
  },
  {
    id: 'nutrition',
    label: 'Nutrition values',
    requirement: 'REQ-4.7.4',
    text: 'Calories, protein, carbohydrates and fat for each food.',
  },
  {
    id: 'categories',
    label: 'Categories',
    requirement: 'REQ-4.7.5',
    text: 'The four meal categories: breakfast, lunch, dinner and snack.',
  },
] as const

export function AdminPage() {
  const [active, setActive] = useState<(typeof SECTIONS)[number]['id']>('foods')
  const section = SECTIONS.find((s) => s.id === active) ?? SECTIONS[0]

  return (
    <>
      <PageHeader
        eyebrow="Administrator"
        title="Admin panel"
        description="Maintain the food, recipe, nutrition and category data that powers the recommendation engine."
      />
      <div className="space-y-6">
        <DevelopmentNotice milestone="catalogue">
          Admin CRUD and role-based access control (REQ-4.7.1) are not implemented yet. This page is
          a layout preview and does not read or change any data.
        </DevelopmentNotice>

        <div role="tablist" aria-label="Admin sections" className="flex flex-wrap gap-2">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              type="button"
              role="tab"
              id={`tab-${s.id}`}
              aria-selected={active === s.id}
              aria-controls={`panel-${s.id}`}
              onClick={() => setActive(s.id)}
              className={cn(
                'rounded-lg px-3 py-2 text-sm font-medium',
                active === s.id
                  ? 'bg-brand-600 text-white'
                  : 'border border-line bg-surface text-ink hover:bg-surface-muted',
              )}
            >
              {s.label}
            </button>
          ))}
        </div>

        <Card role="tabpanel" id={`panel-${section.id}`} aria-labelledby={`tab-${section.id}`}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle>{section.label}</CardTitle>
              <CardDescription>
                {section.text} ({section.requirement})
              </CardDescription>
            </div>
            <Button disabled>Add {section.label.toLowerCase()}</Button>
          </div>
          <EmptyState title={`No ${section.label.toLowerCase()} loaded`} className="mt-5">
            Records will be listed here once the catalogue API is available.
          </EmptyState>
        </Card>
      </div>
    </>
  )
}

import { useState } from 'react'

import { PageHeader } from '../components/layout/PageHeader'
import { CategoriesPanel } from '../features/admin/CategoriesPanel'
import { FoodsPanel } from '../features/admin/FoodsPanel'
import { NutritionPanel } from '../features/admin/NutritionPanel'
import { RecipesPanel } from '../features/admin/RecipesPanel'
import { cn } from '../lib/cn'

const SECTIONS = [
  { id: 'foods', label: 'Foods', Panel: FoodsPanel },
  { id: 'nutrition', label: 'Nutrition values', Panel: NutritionPanel },
  { id: 'recipes', label: 'Recipes', Panel: RecipesPanel },
  { id: 'categories', label: 'Categories', Panel: CategoriesPanel },
] as const

type SectionId = (typeof SECTIONS)[number]['id']

export function AdminPage() {
  const [active, setActive] = useState<SectionId>('foods')
  const section = SECTIONS.find((s) => s.id === active) ?? SECTIONS[0]
  const Panel = section.Panel

  return (
    <>
      <PageHeader
        eyebrow="Administrator"
        title="Admin panel"
        description="Maintain the food, nutrition, recipe and category data that powers the recommendation engine. Changes apply to the next plan that is generated."
      />
      <div role="tablist" aria-label="Admin sections" className="mb-6 flex flex-wrap gap-2">
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
              active === s.id ? 'bg-brand-600 text-white' : 'border border-line bg-surface text-ink hover:bg-surface-muted',
            )}
          >
            {s.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" id={`panel-${section.id}`} aria-labelledby={`tab-${section.id}`}>
        <Panel />
      </div>
    </>
  )
}

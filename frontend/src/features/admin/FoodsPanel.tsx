import { zodResolver } from '@hookform/resolvers/zod'
import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { Alert } from '../../components/ui/Alert'
import { Button } from '../../components/ui/Button'
import { SelectField, TextField } from '../../components/ui/FormField'
import { Modal } from '../../components/ui/Modal'
import { LoadingState } from '../../components/ui/StateViews'
import { useApi } from '../../hooks/useApi'
import { apiClient, errorMessage } from '../../lib/apiClient'
import { DIET_LABELS, formatINR, UNIT_LABELS } from '../../lib/format'
import { toOptions } from '../../lib/options'
import type { Food, NamedRef } from '../../types/api'
import { AdminTable, SearchBox } from './AdminTable'

const foodSchema = z.object({
  name: z.string().trim().min(2, 'Name must be at least 2 characters.').max(100),
  food_group: z.string().min(1, 'Select a food group.'),
  diet_type: z.enum(['vegan', 'vegetarian', 'eggetarian', 'non_vegetarian'], { error: 'Select a diet type.' }),
  unit: z.enum(['g', 'ml', 'piece'], { error: 'Select a unit.' }),
  price_inr: z.number({ error: 'Enter a price.' }).min(0, 'Price cannot be negative.'),
  price_quantity: z.number({ error: 'Enter the quantity the price is for.' }).positive('Must be greater than 0.'),
})
type FoodValues = z.infer<typeof foodSchema>

export function FoodsPanel() {
  const foods = useApi<Food[]>('/admin/foods')
  const groups = useApi<string[]>('/admin/food-groups')
  const allergens = useApi<NamedRef[]>('/allergens')
  const [editing, setEditing] = useState<Food | 'new' | null>(null)
  const [query, setQuery] = useState('')
  const [message, setMessage] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)

  const rows = useMemo(
    () => (foods.data ?? []).filter((f) => f.name.toLowerCase().includes(query.toLowerCase())),
    [foods.data, query],
  )

  async function remove(food: Food) {
    if (!window.confirm(`Delete “${food.name}”? This cannot be undone.`)) return
    try {
      await apiClient.delete(`/admin/foods/${food.id}`)
      setMessage({ tone: 'success', text: `Deleted ${food.name}.` })
      foods.reload()
    } catch (error) {
      setMessage({ tone: 'error', text: errorMessage(error) })
    }
  }

  if (foods.status === 'loading') return <LoadingState />
  if (foods.status === 'error') return <Alert tone="error">{foods.error.message}</Alert>

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <SearchBox label="Search foods" value={query} onChange={setQuery} />
        <Button onClick={() => setEditing('new')}>Add food</Button>
      </div>
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      <AdminTable
        caption="Foods"
        headers={['Food', 'Group', 'Diet', 'Price', 'Allergens', 'Used in', '']}
        rows={rows.map((f) => [
          <span className="font-medium text-ink">{f.name}</span>,
          f.food_group,
          DIET_LABELS[f.diet_type],
          `${formatINR(f.price_inr, true)} / ${Number(f.price_quantity)} ${f.unit}`,
          f.allergens.map((a) => a.name).join(', ') || '—',
          `${f.recipe_count} recipe(s)`,
          <span className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => setEditing(f)}>
              Edit
            </Button>
            <Button size="sm" variant="ghost" onClick={() => remove(f)}>
              Delete
            </Button>
          </span>,
        ])}
        rowKeys={rows.map((f) => f.id)}
      />
      <Modal open={editing !== null} title={editing === 'new' ? 'Add food' : 'Edit food'} onClose={() => setEditing(null)}>
        {editing !== null && (
          <FoodForm
            food={editing === 'new' ? null : editing}
            groups={groups.data ?? []}
            allergens={allergens.data ?? []}
            onSaved={(saved) => {
              setEditing(null)
              setMessage({ tone: 'success', text: `Saved ${saved.name}. Recipes using it were recalculated.` })
              foods.reload()
            }}
          />
        )}
      </Modal>
    </div>
  )
}

function FoodForm({
  food,
  groups,
  allergens,
  onSaved,
}: {
  food: Food | null
  groups: string[]
  allergens: NamedRef[]
  onSaved: (food: Food) => void
}) {
  const [allergenIds, setAllergenIds] = useState<number[]>(food?.allergens.map((a) => a.id) ?? [])
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FoodValues>({
    resolver: zodResolver(foodSchema),
    defaultValues: food
      ? {
          name: food.name,
          food_group: food.food_group,
          diet_type: food.diet_type,
          unit: food.unit,
          price_inr: Number(food.price_inr),
          price_quantity: Number(food.price_quantity),
        }
      : { price_quantity: 1000 },
  })

  async function onSubmit(values: FoodValues) {
    setError(null)
    const body = { ...values, allergen_ids: allergenIds }
    try {
      const saved = food
        ? await apiClient.put<Food>(`/admin/foods/${food.id}`, body)
        : await apiClient.post<Food>('/admin/foods', body)
      onSaved(saved)
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  const num = { valueAsNumber: true } as const
  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)} className="space-y-4" aria-label="Food form">
      {error && <Alert tone="error">{error}</Alert>}
      <TextField label="Name" error={errors.name?.message} {...register('name')} />
      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField
          label="Food group"
          placeholder="Select…"
          options={groups.map((g) => ({ value: g, label: g }))}
          error={errors.food_group?.message}
          {...register('food_group')}
        />
        <SelectField
          label="Diet type"
          placeholder="Select…"
          options={toOptions(DIET_LABELS)}
          error={errors.diet_type?.message}
          {...register('diet_type')}
        />
        <SelectField
          label="Unit"
          placeholder="Select…"
          options={toOptions(UNIT_LABELS)}
          hint="Recipe quantities and nutrition use this unit."
          error={errors.unit?.message}
          {...register('unit')}
        />
        <div className="grid grid-cols-2 gap-2">
          <TextField label="Price (₹)" type="number" step="0.01" error={errors.price_inr?.message} {...register('price_inr', num)} />
          <TextField label="per quantity" type="number" step="0.01" error={errors.price_quantity?.message} {...register('price_quantity', num)} />
        </div>
      </div>
      <fieldset>
        <legend className="text-sm font-medium text-ink">Allergens</legend>
        <div className="mt-2 flex flex-wrap gap-2">
          {allergens.map((a) => (
            <label key={a.id} className="inline-flex items-center gap-2 rounded-full border border-line px-3 py-1 text-sm">
              <input
                type="checkbox"
                className="accent-brand-600"
                checked={allergenIds.includes(a.id)}
                onChange={(e) =>
                  setAllergenIds((ids) => (e.target.checked ? [...ids, a.id] : ids.filter((x) => x !== a.id)))
                }
              />
              {a.name}
            </label>
          ))}
        </div>
      </fieldset>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Saving…' : 'Save food'}
      </Button>
    </form>
  )
}

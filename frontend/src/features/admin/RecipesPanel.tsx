import { zodResolver } from '@hookform/resolvers/zod'
import { useMemo, useState } from 'react'
import { useFieldArray, useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'

import { Alert } from '../../components/ui/Alert'
import { Button } from '../../components/ui/Button'
import { SelectField, TextField } from '../../components/ui/FormField'
import { Modal } from '../../components/ui/Modal'
import { LoadingState } from '../../components/ui/StateViews'
import { useApi } from '../../hooks/useApi'
import { apiClient, errorMessage } from '../../lib/apiClient'
import { DIET_LABELS, formatINR, SLOT_LABELS } from '../../lib/format'
import type { Category, Food, Recipe } from '../../types/api'
import { AdminTable, SearchBox } from './AdminTable'

const recipeSchema = z
  .object({
    name: z.string().trim().min(2, 'Name must be at least 2 characters.').max(120),
    description: z.string().max(2000).optional(),
    category_id: z.number({ error: 'Select a category.' }).int(),
    prep_time_min: z.number({ error: 'Enter the preparation time.' }).int().min(1, 'At least 1 minute.').max(600),
    is_active: z.boolean(),
    ingredients: z
      .array(
        z.object({
          food_id: z.number({ error: 'Select a food.' }).int().positive('Select a food.'),
          quantity: z.number({ error: 'Enter a quantity.' }).positive('Must be greater than 0.'),
        }),
      )
      .min(1, 'Add at least one ingredient.'),
  })
  .refine((v) => new Set(v.ingredients.map((i) => i.food_id)).size === v.ingredients.length, {
    message: 'Each food can appear only once.',
    path: ['ingredients'],
  })
type RecipeValues = z.infer<typeof recipeSchema>

export function RecipesPanel() {
  const recipes = useApi<Recipe[]>('/admin/recipes')
  const foods = useApi<Food[]>('/admin/foods')
  const categories = useApi<Category[]>('/admin/categories')
  const [editing, setEditing] = useState<Recipe | 'new' | null>(null)
  const [query, setQuery] = useState('')
  const [message, setMessage] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)

  const rows = useMemo(
    () => (recipes.data ?? []).filter((r) => r.name.toLowerCase().includes(query.toLowerCase())),
    [recipes.data, query],
  )

  async function remove(recipe: Recipe) {
    if (!window.confirm(`Delete “${recipe.name}”?`)) return
    try {
      await apiClient.delete(`/admin/recipes/${recipe.id}`)
      setMessage({ tone: 'success', text: `Deleted ${recipe.name}.` })
      recipes.reload()
    } catch (error) {
      setMessage({ tone: 'error', text: errorMessage(error) })
    }
  }

  if (recipes.status === 'loading') return <LoadingState />
  if (recipes.status === 'error') return <Alert tone="error">{recipes.error.message}</Alert>

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <SearchBox label="Search recipes" value={query} onChange={setQuery} />
        <Button onClick={() => setEditing('new')}>Add recipe</Button>
      </div>
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      <AdminTable
        caption="Recipes"
        headers={['Recipe', 'Category', 'Diet', 'Prep', 'kcal', 'Cost', 'Status', '']}
        rowKeys={rows.map((r) => r.id)}
        rows={rows.map((r) => [
          <span className="font-medium text-ink">{r.name}</span>,
          SLOT_LABELS[r.slot],
          DIET_LABELS[r.diet_type],
          `${r.prep_time_min} min`,
          r.nutrition ? Math.round(Number(r.nutrition.calories_kcal)) : '—',
          r.nutrition ? formatINR(r.nutrition.estimated_cost_inr, true) : '—',
          r.is_active ? 'Active' : 'Inactive',
          <span className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => setEditing(r)}>
              Edit
            </Button>
            <Button size="sm" variant="ghost" onClick={() => remove(r)}>
              Delete
            </Button>
          </span>,
        ])}
      />
      <Modal wide open={editing !== null} title={editing === 'new' ? 'Add recipe' : 'Edit recipe'} onClose={() => setEditing(null)}>
        {editing !== null && (
          <RecipeForm
            recipe={editing === 'new' ? null : editing}
            foods={foods.data ?? []}
            categories={categories.data ?? []}
            onSaved={(saved) => {
              setEditing(null)
              setMessage({ tone: 'success', text: `Saved ${saved.name}. Nutrition and cost were recalculated.` })
              recipes.reload()
            }}
          />
        )}
      </Modal>
    </div>
  )
}

function RecipeForm({
  recipe,
  foods,
  categories,
  onSaved,
}: {
  recipe: Recipe | null
  foods: Food[]
  categories: Category[]
  onSaved: (recipe: Recipe) => void
}) {
  const [error, setError] = useState<string | null>(null)
  const foodById = useMemo(() => new Map(foods.map((f) => [f.id, f])), [foods])
  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RecipeValues>({
    resolver: zodResolver(recipeSchema),
    defaultValues: recipe
      ? {
          name: recipe.name,
          description: recipe.description ?? '',
          category_id: recipe.category_id,
          prep_time_min: recipe.prep_time_min,
          is_active: recipe.is_active,
          ingredients: recipe.ingredients.map((i) => ({ food_id: i.food_id, quantity: Number(i.quantity) })),
        }
      : { is_active: true, ingredients: [{ food_id: 0, quantity: 100 }], description: '' },
  })
  const { fields, append, remove } = useFieldArray({ control, name: 'ingredients' })
  const ingredients = useWatch({ control, name: 'ingredients' })

  async function onSubmit(values: RecipeValues) {
    setError(null)
    const body = { ...values, description: values.description || null }
    try {
      const saved = recipe
        ? await apiClient.put<Recipe>(`/admin/recipes/${recipe.id}`, body)
        : await apiClient.post<Recipe>('/admin/recipes', body)
      onSaved(saved)
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  const num = { valueAsNumber: true } as const
  const foodOptions = foods.map((f) => ({ value: String(f.id), label: f.name }))
  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)} className="space-y-4" aria-label="Recipe form">
      {error && <Alert tone="error">{error}</Alert>}
      <TextField label="Name" error={errors.name?.message} {...register('name')} />
      <div className="grid gap-4 sm:grid-cols-3">
        <SelectField
          label="Meal category"
          placeholder="Select…"
          options={categories.map((c) => ({ value: String(c.id), label: c.name }))}
          error={errors.category_id?.message}
          {...register('category_id', num)}
        />
        <TextField label="Preparation time (min)" type="number" error={errors.prep_time_min?.message} {...register('prep_time_min', num)} />
        <label className="flex items-center gap-2 self-end pb-2 text-sm font-medium text-ink">
          <input type="checkbox" className="accent-brand-600" {...register('is_active')} />
          Active (can be recommended)
        </label>
      </div>
      <TextField label="Description – optional" error={errors.description?.message} {...register('description')} />

      <fieldset className="space-y-2">
        <legend className="text-sm font-medium text-ink">Ingredients (one serving)</legend>
        {fields.map((field, index) => {
          const unit = foodById.get(Number(ingredients?.[index]?.food_id))?.unit
          return (
            <div key={field.id} className="grid grid-cols-[1fr_8rem_auto] items-start gap-2">
              <SelectField
                label={`Ingredient ${index + 1}`}
                placeholder="Select food…"
                options={foodOptions}
                error={errors.ingredients?.[index]?.food_id?.message}
                {...register(`ingredients.${index}.food_id`, num)}
              />
              <TextField
                label={`Quantity${unit ? ` (${unit})` : ''}`}
                type="number"
                step="0.01"
                error={errors.ingredients?.[index]?.quantity?.message}
                {...register(`ingredients.${index}.quantity`, num)}
              />
              <Button
                variant="ghost"
                size="sm"
                className="mt-7"
                onClick={() => remove(index)}
                disabled={fields.length === 1}
                aria-label={`Remove ingredient ${index + 1}`}
              >
                ✕
              </Button>
            </div>
          )
        })}
        {errors.ingredients?.message && <p className="text-xs font-medium text-danger-700">{errors.ingredients.message}</p>}
        {errors.ingredients?.root?.message && (
          <p className="text-xs font-medium text-danger-700">{errors.ingredients.root.message}</p>
        )}
        <Button variant="secondary" size="sm" onClick={() => append({ food_id: 0, quantity: 100 })}>
          Add ingredient
        </Button>
      </fieldset>
      <p className="text-xs text-ink-muted">
        Nutrition values, estimated cost, diet type and allergens are calculated from the ingredients.
      </p>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Saving…' : 'Save recipe'}
      </Button>
    </form>
  )
}

import { zodResolver } from '@hookform/resolvers/zod'
import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { Alert } from '../../components/ui/Alert'
import { Button } from '../../components/ui/Button'
import { TextField } from '../../components/ui/FormField'
import { Modal } from '../../components/ui/Modal'
import { LoadingState } from '../../components/ui/StateViews'
import { useApi } from '../../hooks/useApi'
import { apiClient, errorMessage } from '../../lib/apiClient'
import type { Food } from '../../types/api'
import { AdminTable, SearchBox } from './AdminTable'

const required = (label: string) => z.number({ error: `${label} is required.` }).min(0, `${label} cannot be negative.`)
const optional = z.number().min(0, 'Cannot be negative.').optional().or(z.nan().transform(() => undefined))

const nutritionSchema = z.object({
  per_quantity: z.number({ error: 'Quantity is required.' }).positive('Must be greater than 0.'),
  calories_kcal: required('Calories'),
  protein_g: required('Protein'),
  carbs_g: required('Carbohydrates'),
  fat_g: required('Fat'),
  fibre_g: optional,
  sugar_g: optional,
  sodium_mg: optional,
  cholesterol_mg: optional,
})
type NutritionValues = z.input<typeof nutritionSchema>
type NutritionOutput = z.output<typeof nutritionSchema>

export function NutritionPanel() {
  const foods = useApi<Food[]>('/admin/nutrition')
  const [editing, setEditing] = useState<Food | null>(null)
  const [query, setQuery] = useState('')
  const [message, setMessage] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const rows = useMemo(
    () => (foods.data ?? []).filter((f) => f.name.toLowerCase().includes(query.toLowerCase())),
    [foods.data, query],
  )

  async function remove(food: Food) {
    if (!window.confirm(`Remove nutrition values for “${food.name}”?`)) return
    try {
      await apiClient.delete(`/admin/foods/${food.id}/nutrition`)
      setMessage({ tone: 'success', text: `Removed nutrition values for ${food.name}.` })
      foods.reload()
    } catch (error) {
      setMessage({ tone: 'error', text: errorMessage(error) })
    }
  }

  if (foods.status === 'loading') return <LoadingState />
  if (foods.status === 'error') return <Alert tone="error">{foods.error.message}</Alert>

  return (
    <div className="space-y-4">
      <SearchBox label="Search foods" value={query} onChange={setQuery} />
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      <AdminTable
        caption="Nutrition values"
        headers={['Food', 'Per', 'kcal', 'Protein', 'Carbs', 'Fat', 'Fibre', 'Sugar', '']}
        rowKeys={rows.map((f) => f.id)}
        rows={rows.map((f) => {
          const n = f.nutrition
          return [
            <span className="font-medium text-ink">{f.name}</span>,
            n ? `${Number(n.per_quantity)} ${f.unit}` : <span className="text-caution-800">Missing</span>,
            n ? Number(n.calories_kcal) : '—',
            n ? `${Number(n.protein_g)} g` : '—',
            n ? `${Number(n.carbs_g)} g` : '—',
            n ? `${Number(n.fat_g)} g` : '—',
            n?.fibre_g != null ? `${Number(n.fibre_g)} g` : '—',
            n?.sugar_g != null ? `${Number(n.sugar_g)} g` : '—',
            <span className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => setEditing(f)}>
                {n ? 'Edit' : 'Add'}
              </Button>
              {n && (
                <Button size="sm" variant="ghost" onClick={() => remove(f)}>
                  Delete
                </Button>
              )}
            </span>,
          ]
        })}
      />
      <Modal open={editing !== null} title={`Nutrition values – ${editing?.name ?? ''}`} onClose={() => setEditing(null)}>
        {editing && (
          <NutritionForm
            food={editing}
            onSaved={() => {
              setMessage({ tone: 'success', text: `Saved nutrition for ${editing.name}. Recipes were recalculated.` })
              setEditing(null)
              foods.reload()
            }}
          />
        )}
      </Modal>
    </div>
  )
}

function NutritionForm({ food, onSaved }: { food: Food; onSaved: () => void }) {
  const [error, setError] = useState<string | null>(null)
  const n = food.nutrition
  const toNum = (v: string | null | undefined) => (v == null ? undefined : Number(v))
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<NutritionValues, unknown, NutritionOutput>({
    resolver: zodResolver(nutritionSchema),
    defaultValues: {
      per_quantity: toNum(n?.per_quantity) ?? (food.unit === 'piece' ? 1 : 100),
      calories_kcal: toNum(n?.calories_kcal),
      protein_g: toNum(n?.protein_g),
      carbs_g: toNum(n?.carbs_g),
      fat_g: toNum(n?.fat_g),
      fibre_g: toNum(n?.fibre_g),
      sugar_g: toNum(n?.sugar_g),
      sodium_mg: toNum(n?.sodium_mg),
      cholesterol_mg: toNum(n?.cholesterol_mg),
    },
  })

  async function onSubmit(values: NutritionOutput) {
    setError(null)
    try {
      await apiClient.put(`/admin/foods/${food.id}/nutrition`, values)
      onSaved()
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  const num = { valueAsNumber: true } as const
  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)} className="space-y-4" aria-label="Nutrition form">
      {error && <Alert tone="error">{error}</Alert>}
      <TextField
        label={`Values are per (${food.unit})`}
        type="number"
        step="0.01"
        error={errors.per_quantity?.message}
        {...register('per_quantity', num)}
      />
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField label="Calories (kcal)" type="number" step="0.01" error={errors.calories_kcal?.message} {...register('calories_kcal', num)} />
        <TextField label="Protein (g)" type="number" step="0.01" error={errors.protein_g?.message} {...register('protein_g', num)} />
        <TextField label="Carbohydrates (g)" type="number" step="0.01" error={errors.carbs_g?.message} {...register('carbs_g', num)} />
        <TextField label="Fat (g)" type="number" step="0.01" error={errors.fat_g?.message} {...register('fat_g', num)} />
        <TextField label="Fibre (g) – optional" type="number" step="0.01" error={errors.fibre_g?.message} {...register('fibre_g', num)} />
        <TextField label="Sugar (g) – optional" type="number" step="0.01" error={errors.sugar_g?.message} {...register('sugar_g', num)} />
        <TextField label="Sodium (mg) – optional" type="number" step="0.01" error={errors.sodium_mg?.message} {...register('sodium_mg', num)} />
        <TextField label="Cholesterol (mg) – optional" type="number" step="0.01" error={errors.cholesterol_mg?.message} {...register('cholesterol_mg', num)} />
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Saving…' : 'Save nutrition values'}
      </Button>
    </form>
  )
}

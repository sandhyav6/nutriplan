import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { Alert } from '../../components/ui/Alert'
import { Button } from '../../components/ui/Button'
import { TextField } from '../../components/ui/FormField'
import { Modal } from '../../components/ui/Modal'
import { LoadingState } from '../../components/ui/StateViews'
import { useApi } from '../../hooks/useApi'
import { apiClient, errorMessage } from '../../lib/apiClient'
import { SLOT_LABELS } from '../../lib/format'
import type { Category } from '../../types/api'
import { AdminTable } from './AdminTable'

const categorySchema = z.object({
  name: z.string().trim().min(2, 'Name must be at least 2 characters.').max(50),
  description: z.string().max(255).optional(),
})
type CategoryValues = z.infer<typeof categorySchema>

export function CategoriesPanel() {
  const categories = useApi<Category[]>('/admin/categories')
  const [editing, setEditing] = useState<Category | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  if (categories.status === 'loading') return <LoadingState />
  if (categories.status === 'error') return <Alert tone="error">{categories.error.message}</Alert>

  return (
    <div className="space-y-4">
      <Alert tone="info">
        NutriPlan uses exactly four meal categories so every weekly plan has the same structure
        (SRS §2.5). You can rename them and edit their descriptions, but not add or delete them.
      </Alert>
      {message && <Alert tone="success">{message}</Alert>}
      <AdminTable
        caption="Meal categories"
        headers={['Plan slot', 'Name', 'Description', 'Recipes', '']}
        rowKeys={categories.data.map((c) => c.id)}
        rows={categories.data.map((c) => [
          SLOT_LABELS[c.slot],
          <span className="font-medium text-ink">{c.name}</span>,
          c.description || '—',
          c.recipe_count,
          <Button size="sm" variant="secondary" onClick={() => setEditing(c)}>
            Edit
          </Button>,
        ])}
      />
      <Modal open={editing !== null} title="Edit category" onClose={() => setEditing(null)}>
        {editing && (
          <CategoryForm
            category={editing}
            onSaved={(saved) => {
              setEditing(null)
              setMessage(`Saved ${saved.name}.`)
              categories.reload()
            }}
          />
        )}
      </Modal>
    </div>
  )
}

function CategoryForm({ category, onSaved }: { category: Category; onSaved: (c: Category) => void }) {
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CategoryValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: { name: category.name, description: category.description ?? '' },
  })

  async function onSubmit(values: CategoryValues) {
    setError(null)
    try {
      onSaved(
        await apiClient.put<Category>(`/admin/categories/${category.id}`, {
          name: values.name,
          description: values.description || null,
        }),
      )
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)} className="space-y-4" aria-label="Category form">
      {error && <Alert tone="error">{error}</Alert>}
      <TextField label="Name" error={errors.name?.message} {...register('name')} />
      <TextField label="Description" error={errors.description?.message} {...register('description')} />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Saving…' : 'Save category'}
      </Button>
    </form>
  )
}

import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'

import { PageHeader } from '../components/layout/PageHeader'
import { Alert } from '../components/ui/Alert'
import { Button, ButtonLink } from '../components/ui/Button'
import { Card, CardTitle } from '../components/ui/Card'
import { SelectField, TextField } from '../components/ui/FormField'
import { LoadingState } from '../components/ui/StateViews'
import { FoodExclusionPicker } from '../features/profile/FoodExclusionPicker'
import { NutritionSummary } from '../features/profile/NutritionSummary'
import { profileSchema, type ProfileFormValues } from '../features/profile/schema'
import { useApi } from '../hooks/useApi'
import { useAuth } from '../hooks/useAuth'
import { apiClient, ApiError, errorMessage, fieldErrors } from '../lib/apiClient'
import { ACTIVITY_LABELS, DIET_LABELS, GENDER_LABELS, GOAL_LABELS } from '../lib/format'
import { toOptions } from '../lib/options'
import type { NamedRef, Profile, ProfileInput } from '../types/api'

const ONBOARDING = [
  'Tell us about yourself – age, body measurements and how active you are.',
  'Choose your diet and declare allergies. Allergens are never included in your meals.',
  'Set your goal, weekly grocery budget and how long you can spend cooking each meal.',
  'Save, then generate your first weekly meal plan and grocery list.',
]

function toFormValues(p: Profile): ProfileFormValues {
  return {
    age: p.age,
    gender: p.gender,
    height_cm: Number(p.height_cm),
    weight_kg: Number(p.weight_kg),
    activity_level: p.activity_level,
    dietary_preference: p.dietary_preference,
    health_goal: p.health_goal,
    weekly_budget_inr: Number(p.weekly_budget_inr),
    max_cooking_time_min: p.max_cooking_time_min,
  }
}

export function ProfilePage() {
  const profile = useApi<Profile>('/profile')
  if (profile.status === 'loading') return <LoadingState label="Loading your profile…" />
  if (profile.status === 'error' && profile.error.status !== 404) {
    return <Alert tone="error">{profile.error.message}</Alert>
  }
  return <ProfileEditor initial={profile.status === 'success' ? profile.data : null} />
}

function ProfileEditor({ initial }: { initial: Profile | null }) {
  const { setHasProfile } = useAuth()
  const allergens = useApi<NamedRef[]>('/allergens')
  const foods = useApi<NamedRef[]>('/foods')
  const [allergenIds, setAllergenIds] = useState<number[]>(initial?.allergens.map((a) => a.id) ?? [])
  const [excludedIds, setExcludedIds] = useState<number[]>(initial?.excluded_foods.map((f) => f.id) ?? [])
  const [saved, setSaved] = useState<Profile | null>(initial)
  const [message, setMessage] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const isNew = initial === null

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: initial ? toFormValues(initial) : undefined,
  })

  async function onSubmit(values: ProfileFormValues) {
    setMessage(null)
    const payload: ProfileInput = { ...values, allergen_ids: allergenIds, excluded_food_ids: excludedIds }
    try {
      const result = await apiClient.put<Profile>('/profile', payload)
      setSaved(result)
      setHasProfile(true)
      setMessage({ tone: 'success', text: 'Profile saved. Your nutrition targets are up to date.' })
    } catch (error) {
      const fields = fieldErrors(error)
      for (const [name, text] of Object.entries(fields)) {
        if (name in profileSchema.shape) setError(name as keyof ProfileFormValues, { message: text })
      }
      setMessage({ tone: 'error', text: error instanceof ApiError ? error.message : errorMessage(error) })
    }
  }

  const numberField = { valueAsNumber: true } as const

  return (
    <>
      <PageHeader
        eyebrow="Profile"
        title={isNew && !saved ? 'Set up your nutrition profile' : 'Your profile'}
        description="These details become your nutrition target (BMI, daily calories and protein) before any meals are recommended. You can change them at any time."
      />

      {isNew && !saved && (
        <Card className="mb-6 bg-brand-50/60">
          <CardTitle>Getting started</CardTitle>
          <ol className="mt-3 grid gap-3 sm:grid-cols-2">
            {ONBOARDING.map((step, i) => (
              <li key={step} className="flex gap-3 text-sm text-ink">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-600 text-xs font-semibold text-white">
                  {i + 1}
                </span>
                {step}
              </li>
            ))}
          </ol>
        </Card>
      )}


      <form aria-label="Profile form" noValidate onSubmit={handleSubmit(onSubmit)} className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="space-y-6">
          <Card>
            <CardTitle>About you</CardTitle>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <TextField label="Age" type="number" inputMode="numeric" error={errors.age?.message} {...register('age', numberField)} />
              <SelectField
                label="Gender"
                placeholder="Select…"
                options={toOptions(GENDER_LABELS)}
                error={errors.gender?.message}
                {...register('gender')}
              />
              <TextField
                label="Height (cm)"
                type="number"
                step="0.1"
                inputMode="decimal"
                error={errors.height_cm?.message}
                {...register('height_cm', numberField)}
              />
              <TextField
                label="Weight (kg)"
                type="number"
                step="0.1"
                inputMode="decimal"
                error={errors.weight_kg?.message}
                {...register('weight_kg', numberField)}
              />
              <SelectField
                label="Activity level"
                placeholder="Select…"
                options={toOptions(ACTIVITY_LABELS)}
                hint="Sedentary ≈ 1800, moderately active ≈ 2300, very active ≈ 2800 kcal/day."
                error={errors.activity_level?.message}
                {...register('activity_level')}
              />
            </div>
          </Card>

          <Card>
            <CardTitle>Diet and allergies</CardTitle>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <SelectField
                label="Dietary preference"
                placeholder="Select…"
                options={toOptions(DIET_LABELS)}
                error={errors.dietary_preference?.message}
                {...register('dietary_preference')}
              />
            </div>
            <fieldset className="mt-5">
              <legend className="text-sm font-medium text-ink">Declared allergies</legend>
              <p className="text-xs text-ink-muted">Meals containing these are never recommended.</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {(allergens.data ?? []).map((a) => {
                  const checked = allergenIds.includes(a.id)
                  return (
                    <label
                      key={a.id}
                      className={`inline-flex cursor-pointer items-center gap-2 rounded-full border px-3 py-1.5 text-sm ${
                        checked ? 'border-brand-500 bg-brand-50 text-brand-800' : 'border-line bg-surface text-ink'
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="accent-brand-600"
                        checked={checked}
                        onChange={() =>
                          setAllergenIds((ids) => (checked ? ids.filter((x) => x !== a.id) : [...ids, a.id]))
                        }
                      />
                      {a.name}
                    </label>
                  )
                })}
              </div>
            </fieldset>
            <div className="mt-5">
              <FoodExclusionPicker foods={foods.data ?? []} selected={excludedIds} onChange={setExcludedIds} />
            </div>
          </Card>

          <Card>
            <CardTitle>Goals and constraints</CardTitle>
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <SelectField
                label="Health goal"
                placeholder="Select…"
                options={toOptions(GOAL_LABELS)}
                error={errors.health_goal?.message}
                {...register('health_goal')}
              />
              <TextField
                label="Weekly budget (₹)"
                type="number"
                inputMode="decimal"
                error={errors.weekly_budget_inr?.message}
                {...register('weekly_budget_inr', numberField)}
              />
              <TextField
                label="Cooking time per meal (min)"
                type="number"
                inputMode="numeric"
                error={errors.max_cooking_time_min?.message}
                {...register('max_cooking_time_min', numberField)}
              />
            </div>
          </Card>

          {message && <Alert tone={message.tone}>{message.text}</Alert>}
          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving…' : 'Save profile'}
            </Button>
            {saved && (
              <ButtonLink to="/meal-plan" variant="secondary">
                Go to my meal plan
              </ButtonLink>
            )}
          </div>
        </div>

        <NutritionSummary nutrition={saved?.nutrition ?? null} />
      </form>
    </>
  )
}

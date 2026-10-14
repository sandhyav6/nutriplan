import type {
  ActivityLevel,
  DietType,
  FeedbackType,
  Gender,
  HealthGoal,
  MealSlot,
  Unit,
} from '../types/api'

const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
const inrPrecise = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})
const number = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 })

export const formatINR = (value: string | number, precise = false) =>
  (precise ? inrPrecise : inr).format(Number(value))
export const formatNumber = (value: string | number) => number.format(Number(value))
export const formatKcal = (value: string | number) => `${Math.round(Number(value)).toLocaleString('en-IN')} kcal`

export function formatDate(iso: string, options: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' }) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('en-IN', options)
}

export function formatQuantity(quantity: string | number, unit: Unit): string {
  const q = Number(quantity)
  if (unit === 'piece') return `${number.format(q)} ${q === 1 ? 'piece' : 'pieces'}`
  if (q >= 1000) return `${number.format(q / 1000)} ${unit === 'g' ? 'kg' : 'L'}`
  return `${Math.round(q)} ${unit}`
}

export const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] as const

export const SLOT_LABELS: Record<MealSlot, string> = {
  breakfast: 'Breakfast',
  lunch: 'Lunch',
  dinner: 'Dinner',
  snack: 'Snack',
}
export const SLOTS: MealSlot[] = ['breakfast', 'lunch', 'dinner', 'snack']

export const GENDER_LABELS: Record<Gender, string> = { male: 'Male', female: 'Female', other: 'Other' }
export const ACTIVITY_LABELS: Record<ActivityLevel, string> = {
  sedentary: 'Sedentary',
  moderately_active: 'Moderately active',
  very_active: 'Very active',
}
export const DIET_LABELS: Record<DietType, string> = {
  vegan: 'Vegan',
  vegetarian: 'Vegetarian',
  eggetarian: 'Eggetarian',
  non_vegetarian: 'Non-vegetarian',
}
export const GOAL_LABELS: Record<HealthGoal, string> = {
  weight_loss: 'Weight loss',
  muscle_gain: 'Muscle gain',
  maintenance: 'Maintenance',
}
export const FEEDBACK_LABELS: Record<FeedbackType, string> = {
  favourite: 'Favourite',
  like: 'Like',
  skip: 'Skip',
  dislike: 'Dislike',
}
export const UNIT_LABELS: Record<Unit, string> = { g: 'grams (g)', ml: 'millilitres (ml)', piece: 'pieces' }

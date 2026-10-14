import { z } from 'zod'

/** Mirrors backend/app/schemas/profile.py (REQ-4.1.3, REQ-4.1.4). */
const num = (label: string) => z.number({ error: `${label} is required.` })

export const profileSchema = z.object({
  age: num('Age').int('Age must be a whole number.').min(13, 'Age must be at least 13.').max(100, 'Age must be at most 100.'),
  gender: z.enum(['male', 'female', 'other'], { error: 'Select a gender.' }),
  height_cm: num('Height').min(100, 'Height must be between 100 and 250 cm.').max(250, 'Height must be between 100 and 250 cm.'),
  weight_kg: num('Weight').min(25, 'Weight must be between 25 and 300 kg.').max(300, 'Weight must be between 25 and 300 kg.'),
  activity_level: z.enum(['sedentary', 'moderately_active', 'very_active'], { error: 'Select an activity level.' }),
  dietary_preference: z.enum(['vegan', 'vegetarian', 'eggetarian', 'non_vegetarian'], {
    error: 'Select a dietary preference.',
  }),
  health_goal: z.enum(['weight_loss', 'muscle_gain', 'maintenance'], { error: 'Select a health goal.' }),
  weekly_budget_inr: num('Weekly budget').min(100, 'Weekly budget must be at least ₹100.').max(100000, 'Weekly budget must be at most ₹1,00,000.'),
  max_cooking_time_min: num('Cooking time')
    .int('Cooking time must be a whole number of minutes.')
    .min(5, 'Cooking time must be at least 5 minutes.')
    .max(240, 'Cooking time must be at most 240 minutes.'),
})

export type ProfileFormValues = z.infer<typeof profileSchema>

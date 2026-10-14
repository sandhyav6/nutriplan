/** API contracts – mirror backend/app/schemas. Decimals arrive as strings. */

export interface ApiErrorBody {
  error: { code: string; message: string; details?: unknown }
}

export interface HealthResponse {
  status: 'ok' | 'degraded'
  service: string
  version: string
  environment: string
  database: 'ok' | 'unavailable'
}

export type Role = 'user' | 'admin'
export type Gender = 'male' | 'female' | 'other'
export type ActivityLevel = 'sedentary' | 'moderately_active' | 'very_active'
export type DietaryPreference = 'vegan' | 'vegetarian' | 'eggetarian' | 'non_vegetarian'
export type DietType = DietaryPreference
export type HealthGoal = 'weight_loss' | 'muscle_gain' | 'maintenance'
export type MealSlot = 'breakfast' | 'lunch' | 'dinner' | 'snack'
export type Unit = 'g' | 'ml' | 'piece'
export type FeedbackType = 'favourite' | 'like' | 'skip' | 'dislike'

export interface User {
  id: number
  email: string
  full_name: string
  role: Role
  created_at: string
}

export interface SessionResponse {
  user: User
  has_profile: boolean
}

export interface NamedRef {
  id: number
  name: string
}

export interface NutritionTarget {
  bmi: string
  bmi_category: string
  baseline_calories_kcal: number
  daily_calories_kcal: number
  daily_protein_g: number
  prioritise_weight_loss_meals: boolean
}

export interface ProfileInput {
  age: number
  gender: Gender
  height_cm: number
  weight_kg: number
  activity_level: ActivityLevel
  dietary_preference: DietaryPreference
  health_goal: HealthGoal
  weekly_budget_inr: number
  max_cooking_time_min: number
  allergen_ids: number[]
  excluded_food_ids: number[]
}

export interface Profile extends Omit<ProfileInput, 'height_cm' | 'weight_kg' | 'weekly_budget_inr' | 'allergen_ids' | 'excluded_food_ids'> {
  id: number
  height_cm: string
  weight_kg: string
  weekly_budget_inr: string
  allergens: NamedRef[]
  excluded_foods: NamedRef[]
  updated_at: string
  nutrition: NutritionTarget
}

export interface MealSummary {
  recipe_id: number
  name: string
  prep_time_min: number
  diet_type: DietType
  servings: string
  calories_kcal: string
  protein_g: string
  carbs_g: string
  fat_g: string
  cost_inr: string
}

export interface PlannedMeal {
  id: number
  day_of_week: number
  date: string
  slot: MealSlot
  meal: MealSummary | null
  unavailable_reason: string | null
  feedback: FeedbackType | null
}

export interface DayTotals {
  day_of_week: number
  date: string
  calories_kcal: string
  protein_g: string
  cost_inr: string
}

export interface PlanNote {
  code: string
  message: string
}

export interface MealPlan {
  id: number
  week_start_date: string
  generated_at: string
  total_calories_kcal: string
  total_cost_inr: string
  weekly_budget_inr: string
  nutrition: NutritionTarget
  notes: PlanNote[]
  profile_changed_since_generation: boolean
  meals: PlannedMeal[]
  days: DayTotals[]
}

export interface IngredientLine {
  food_id: number
  name: string
  quantity: string
  unit: Unit
  food_group: string
}

export interface MealDetail extends PlannedMeal {
  description: string | null
  category_name: string | null
  allergens: string[]
  ingredients: IngredientLine[]
  sugar_g: string | null
  fibre_g: string | null
}

export interface ReplaceResult {
  meal: MealDetail
  total_calories_kcal: string
  total_cost_inr: string
}

export interface GroceryItem {
  food_id: number
  name: string
  food_group: string
  quantity: string
  unit: Unit
  display_quantity: string
  estimated_cost_inr: string
}

export interface GroceryList {
  id: number
  meal_plan_id: number
  week_start_date: string
  generated_at: string
  total_estimated_cost_inr: string
  weekly_budget_inr: string
  item_count: number
  groups: { food_group: string; items: GroceryItem[]; subtotal_inr: string }[]
}

export interface Dashboard {
  has_plan: boolean
  week_start_date: string | null
  nutrition: NutritionTarget | null
  weekly_budget_inr: string | null
  total_calories_kcal: string
  average_daily_calories_kcal: string
  average_daily_protein_g: string
  estimated_spend_inr: string
  days: DayTotals[]
  meals_by_slot: Partial<Record<MealSlot, number>>
  unavailable_slots: number
  feedback_on_plan: Partial<Record<FeedbackType | 'none', number>>
  total_feedback_events: number
  favourites: { recipe_id: number; name: string; slot: MealSlot }[]
}

// ----- admin
export interface FoodNutrition {
  id: number
  food_id: number
  per_quantity: string
  calories_kcal: string
  protein_g: string
  carbs_g: string
  fat_g: string
  fibre_g: string | null
  sugar_g: string | null
  sodium_mg: string | null
  cholesterol_mg: string | null
}

export interface Food {
  id: number
  name: string
  food_group: string
  diet_type: DietType
  unit: Unit
  price_inr: string
  price_quantity: string
  allergens: NamedRef[]
  nutrition: FoodNutrition | null
  recipe_count: number
  updated_at: string
}

export interface Recipe {
  id: number
  name: string
  description: string | null
  category_id: number
  category_name: string
  slot: MealSlot
  prep_time_min: number
  is_active: boolean
  diet_type: DietType
  allergens: string[]
  ingredients: { food_id: number; food_name: string; quantity: string; unit: Unit; food_group: string }[]
  nutrition: {
    calories_kcal: string
    protein_g: string
    carbs_g: string
    fat_g: string
    fibre_g: string | null
    sugar_g: string | null
    estimated_cost_inr: string
  } | null
  updated_at: string
}

export interface Category {
  id: number
  slot: MealSlot
  name: string
  description: string | null
  display_order: number
  recipe_count: number
}

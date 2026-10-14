import type { Dashboard, GroceryList, MealDetail, MealPlan, NutritionTarget, PlannedMeal, Profile } from '../types/api'

export const NUTRITION: NutritionTarget = {
  bmi: '21.5',
  bmi_category: 'normal',
  baseline_calories_kcal: 2300,
  daily_calories_kcal: 2300,
  daily_protein_g: 44,
  prioritise_weight_loss_meals: false,
}

export const PROFILE: Profile = {
  id: 1,
  age: 21,
  gender: 'female',
  height_cm: '160.0',
  weight_kg: '55.0',
  activity_level: 'moderately_active',
  dietary_preference: 'vegetarian',
  health_goal: 'maintenance',
  weekly_budget_inr: '1500.00',
  max_cooking_time_min: 30,
  allergens: [{ id: 1, name: 'Peanuts' }],
  excluded_foods: [],
  updated_at: '2026-10-12T08:00:00Z',
  nutrition: NUTRITION,
}

const SLOTS = ['breakfast', 'lunch', 'dinner', 'snack'] as const

export function plannedMeal(day: number, slotIndex: number): PlannedMeal {
  const id = day * 4 + slotIndex + 1
  if (day === 6 && slotIndex === 2) {
    return {
      id,
      day_of_week: day,
      date: '2026-10-18',
      slot: 'dinner',
      meal: null,
      unavailable_reason: 'No safe dinner recipe can be prepared within 10 minutes.',
      feedback: null,
    }
  }
  return {
    id,
    day_of_week: day,
    date: `2026-10-${12 + day}`,
    slot: SLOTS[slotIndex],
    meal: {
      recipe_id: 100 + id,
      name: `Meal ${id}`,
      prep_time_min: 15,
      diet_type: 'vegetarian',
      servings: '1.25',
      calories_kcal: '575',
      protein_g: '20.0',
      carbs_g: '70.0',
      fat_g: '15.0',
      cost_inr: '30.00',
    },
    unavailable_reason: null,
    feedback: id === 1 ? 'favourite' : null,
  }
}

export const PLAN: MealPlan = {
  id: 7,
  week_start_date: '2026-10-12',
  generated_at: '2026-10-12T09:00:00Z',
  total_calories_kcal: '15525',
  total_cost_inr: '810.00',
  weekly_budget_inr: '1500.00',
  nutrition: NUTRITION,
  notes: [{ code: 'unavailable', message: 'Dinner: No safe dinner recipe can be prepared within 10 minutes.' }],
  profile_changed_since_generation: false,
  meals: Array.from({ length: 7 }, (_, d) => SLOTS.map((_, s) => plannedMeal(d, s))).flat(),
  days: Array.from({ length: 7 }, (_, d) => ({
    day_of_week: d,
    date: `2026-10-${12 + d}`,
    calories_kcal: '2300',
    protein_g: '80',
    cost_inr: '120',
  })),
}

export const MEAL_DETAIL: MealDetail = {
  ...plannedMeal(0, 1),
  feedback: null,
  description: null,
  category_name: 'Lunch',
  allergens: ['Dairy'],
  ingredients: [
    { food_id: 1, name: 'Rice', quantity: '100.00', unit: 'g', food_group: 'Grains & Cereals' },
    { food_id: 2, name: 'Curd', quantity: '250.00', unit: 'g', food_group: 'Dairy & Alternatives' },
  ],
  sugar_g: '6.0',
  fibre_g: '3.1',
}

export const GROCERY: GroceryList = {
  id: 3,
  meal_plan_id: 7,
  week_start_date: '2026-10-12',
  generated_at: '2026-10-12T09:00:00Z',
  total_estimated_cost_inr: '812.40',
  weekly_budget_inr: '1500.00',
  item_count: 2,
  groups: [
    {
      food_group: 'Grains & Cereals',
      subtotal_inr: '60.00',
      items: [
        {
          food_id: 1,
          name: 'Rice',
          food_group: 'Grains & Cereals',
          quantity: '1250.00',
          unit: 'g',
          display_quantity: '1.25 kg',
          estimated_cost_inr: '60.00',
        },
      ],
    },
    {
      food_group: 'Fruits',
      subtotal_inr: '42.00',
      items: [
        {
          food_id: 2,
          name: 'Banana',
          food_group: 'Fruits',
          quantity: '7.00',
          unit: 'piece',
          display_quantity: '7 pieces',
          estimated_cost_inr: '42.00',
        },
      ],
    },
  ],
}

export const DASHBOARD: Dashboard = {
  has_plan: true,
  week_start_date: '2026-10-12',
  nutrition: NUTRITION,
  weekly_budget_inr: '1500.00',
  total_calories_kcal: '15525',
  average_daily_calories_kcal: '2218',
  average_daily_protein_g: '80.0',
  estimated_spend_inr: '812.40',
  days: PLAN.days,
  meals_by_slot: { breakfast: 7, lunch: 7, dinner: 6, snack: 7 },
  unavailable_slots: 1,
  feedback_on_plan: { favourite: 1, like: 2, skip: 0, dislike: 1, none: 23 },
  total_feedback_events: 4,
  favourites: [{ recipe_id: 101, name: 'Meal 1', slot: 'breakfast' }],
}

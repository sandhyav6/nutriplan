/** Profile field options – mirror backend/app/models/enums.py and the SRS (REQ-4.1.3). */
export const GENDERS = ['Male', 'Female', 'Other'] as const
export const ACTIVITY_LEVELS = ['Sedentary', 'Moderately active', 'Very active'] as const
export const DIETARY_PREFERENCES = ['Vegan', 'Vegetarian', 'Eggetarian', 'Non-vegetarian'] as const
export const HEALTH_GOALS = ['Weight loss', 'Muscle gain', 'Maintenance'] as const
export const ALLERGENS = [
  'Peanuts',
  'Tree Nuts',
  'Dairy',
  'Egg',
  'Gluten',
  'Soy',
  'Fish',
  'Shellfish',
  'Sesame',
  'Mustard',
] as const

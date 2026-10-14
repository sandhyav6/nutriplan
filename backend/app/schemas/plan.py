"""Meal plan, grocery list, feedback and dashboard contracts."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DietType, FeedbackType, MealSlot, MeasurementUnit
from app.schemas.profile import NutritionTargetOut


class MealSummary(BaseModel):
    recipe_id: int
    name: str
    prep_time_min: int
    diet_type: DietType
    servings: Decimal
    calories_kcal: Decimal
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal
    cost_inr: Decimal


class PlannedMealOut(BaseModel):
    id: int
    day_of_week: int
    date: date
    slot: MealSlot
    meal: MealSummary | None
    unavailable_reason: str | None
    feedback: FeedbackType | None


class DayTotals(BaseModel):
    day_of_week: int
    date: date
    calories_kcal: Decimal
    protein_g: Decimal
    cost_inr: Decimal


class PlanNoteOut(BaseModel):
    code: str
    message: str


class MealPlanOut(BaseModel):
    id: int
    week_start_date: date
    generated_at: datetime
    total_calories_kcal: Decimal
    total_cost_inr: Decimal
    weekly_budget_inr: Decimal
    nutrition: NutritionTargetOut
    notes: list[PlanNoteOut]
    profile_changed_since_generation: bool
    meals: list[PlannedMealOut]
    days: list[DayTotals]


class IngredientLine(BaseModel):
    food_id: int
    name: str
    quantity: Decimal
    unit: MeasurementUnit
    food_group: str


class MealDetailOut(PlannedMealOut):
    description: str | None
    category_name: str | None
    allergens: list[str]
    ingredients: list[IngredientLine]
    sugar_g: Decimal | None
    fibre_g: Decimal | None


class ReplaceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Recipes already swapped out of this slot – avoided while alternatives remain.
    avoid_recipe_ids: list[int] = Field(default_factory=list, max_length=100)


class ReplaceResultOut(BaseModel):
    meal: MealDetailOut
    total_calories_kcal: Decimal
    total_cost_inr: Decimal


class GroceryItemOut(BaseModel):
    food_id: int
    name: str
    food_group: str
    quantity: Decimal
    unit: MeasurementUnit
    display_quantity: str
    estimated_cost_inr: Decimal


class GroceryGroupOut(BaseModel):
    food_group: str
    items: list[GroceryItemOut]
    subtotal_inr: Decimal


class GroceryListOut(BaseModel):
    id: int
    meal_plan_id: int
    week_start_date: date
    generated_at: datetime
    total_estimated_cost_inr: Decimal
    weekly_budget_inr: Decimal
    item_count: int
    groups: list[GroceryGroupOut]


class FeedbackIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    planned_meal_id: int
    feedback_type: FeedbackType


class FeedbackOut(BaseModel):
    id: int
    planned_meal_id: int | None
    recipe_id: int
    feedback_type: FeedbackType
    score: int
    created_at: datetime


class FavouriteOut(BaseModel):
    recipe_id: int
    name: str
    slot: MealSlot


class DashboardOut(BaseModel):
    has_plan: bool
    week_start_date: date | None
    nutrition: NutritionTargetOut | None
    weekly_budget_inr: Decimal | None
    total_calories_kcal: Decimal
    average_daily_calories_kcal: Decimal
    average_daily_protein_g: Decimal
    estimated_spend_inr: Decimal
    days: list[DayTotals]
    meals_by_slot: dict[str, int]
    unavailable_slots: int
    feedback_on_plan: dict[str, int]
    total_feedback_events: int
    favourites: list[FavouriteOut]

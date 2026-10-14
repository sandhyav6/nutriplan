"""Profile contracts (REQ-4.1.3, REQ-4.1.4). Ranges match the database CHECK constraints."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ActivityLevel, DietaryPreference, Gender, HealthGoal


class ProfileIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=13, le=100)
    gender: Gender
    height_cm: Decimal = Field(ge=100, le=250, decimal_places=1)
    weight_kg: Decimal = Field(ge=25, le=300, decimal_places=1)
    activity_level: ActivityLevel
    dietary_preference: DietaryPreference
    health_goal: HealthGoal
    weekly_budget_inr: Decimal = Field(ge=100, le=100000, decimal_places=2)
    max_cooking_time_min: int = Field(ge=5, le=240)
    allergen_ids: list[int] = Field(default_factory=list, max_length=50)
    excluded_food_ids: list[int] = Field(default_factory=list, max_length=100)

    @field_validator("allergen_ids", "excluded_food_ids")
    @classmethod
    def unique_ids(cls, value: list[int]) -> list[int]:
        return sorted(set(value))


class NamedRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class NutritionTargetOut(BaseModel):
    bmi: Decimal
    bmi_category: str
    baseline_calories_kcal: int
    daily_calories_kcal: int
    daily_protein_g: int
    prioritise_weight_loss_meals: bool


class ProfileOut(BaseModel):
    id: int
    age: int
    gender: Gender
    height_cm: Decimal
    weight_kg: Decimal
    activity_level: ActivityLevel
    dietary_preference: DietaryPreference
    health_goal: HealthGoal
    weekly_budget_inr: Decimal
    max_cooking_time_min: int
    allergens: list[NamedRef]
    excluded_foods: list[NamedRef]
    updated_at: datetime
    nutrition: NutritionTargetOut

"""Admin catalogue contracts (REQ-4.7.2 – REQ-4.7.5)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import DietType, MealSlot, MeasurementUnit
from app.schemas.profile import NamedRef

FOOD_GROUPS = [
    "Grains & Cereals",
    "Pulses & Legumes",
    "Dairy & Alternatives",
    "Eggs, Meat & Seafood",
    "Vegetables",
    "Fruits",
    "Nuts & Seeds",
    "Oils & Fats",
    "Spices & Condiments",
    "Sweeteners",
]


class NutritionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    per_quantity: Decimal = Field(gt=0, le=10000)
    calories_kcal: Decimal = Field(ge=0, le=100000)
    protein_g: Decimal = Field(ge=0, le=10000)
    carbs_g: Decimal = Field(ge=0, le=10000)
    fat_g: Decimal = Field(ge=0, le=10000)
    fibre_g: Decimal | None = Field(default=None, ge=0, le=10000)
    sugar_g: Decimal | None = Field(default=None, ge=0, le=10000)
    sodium_mg: Decimal | None = Field(default=None, ge=0, le=100000)
    cholesterol_mg: Decimal | None = Field(default=None, ge=0, le=100000)


class NutritionOut(NutritionIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    food_id: int


class FoodIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=100)
    food_group: str
    diet_type: DietType
    unit: MeasurementUnit
    price_inr: Decimal = Field(ge=0, le=1000000, decimal_places=2)
    price_quantity: Decimal = Field(gt=0, le=100000)
    allergen_ids: list[int] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("food_group")
    @classmethod
    def known_group(cls, value: str) -> str:
        if value not in FOOD_GROUPS:
            raise ValueError(f"Food group must be one of: {', '.join(FOOD_GROUPS)}.")
        return value


class FoodOut(BaseModel):
    id: int
    name: str
    food_group: str
    diet_type: DietType
    unit: MeasurementUnit
    price_inr: Decimal
    price_quantity: Decimal
    allergens: list[NamedRef]
    nutrition: NutritionOut | None
    recipe_count: int
    updated_at: datetime


class IngredientIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    food_id: int
    quantity: Decimal = Field(gt=0, le=100000)


class RecipeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    category_id: int
    prep_time_min: int = Field(ge=1, le=600)
    is_active: bool = True
    ingredients: list[IngredientIn] = Field(min_length=1, max_length=40)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("ingredients")
    @classmethod
    def unique_foods(cls, value: list[IngredientIn]) -> list[IngredientIn]:
        ids = [i.food_id for i in value]
        if len(ids) != len(set(ids)):
            raise ValueError("Each food can appear only once in a recipe.")
        return value


class IngredientOut(BaseModel):
    food_id: int
    food_name: str
    quantity: Decimal
    unit: MeasurementUnit
    food_group: str


class RecipeNutritionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    calories_kcal: Decimal
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal
    fibre_g: Decimal | None
    sugar_g: Decimal | None
    estimated_cost_inr: Decimal


class RecipeOut(BaseModel):
    id: int
    name: str
    description: str | None
    category_id: int
    category_name: str
    slot: MealSlot
    prep_time_min: int
    is_active: bool
    diet_type: DietType
    allergens: list[str]
    ingredients: list[IngredientOut]
    nutrition: RecipeNutritionOut | None
    updated_at: datetime


class CategoryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=255)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slot: MealSlot
    name: str
    description: str | None
    display_order: int
    recipe_count: int = 0

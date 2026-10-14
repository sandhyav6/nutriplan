"""Plain, immutable data types exchanged with the rule engine (no ORM objects)."""

from dataclasses import dataclass, field
from decimal import Decimal

from app.models.enums import ActivityLevel, DietaryPreference, DietType, HealthGoal, MealSlot


@dataclass(frozen=True, slots=True)
class ProfileInput:
    """Stage 1 – validated user inputs."""

    age: int
    height_cm: Decimal
    weight_kg: Decimal
    activity_level: ActivityLevel
    dietary_preference: DietaryPreference
    health_goal: HealthGoal
    weekly_budget_inr: Decimal
    max_cooking_time_min: int
    allergen_ids: frozenset[int] = frozenset()
    excluded_food_ids: frozenset[int] = frozenset()


@dataclass(frozen=True, slots=True)
class NutritionTarget:
    """Stage 2 – numeric targets derived from the profile."""

    bmi: Decimal
    bmi_category: str
    baseline_calories_kcal: int
    daily_calories_kcal: int
    daily_protein_g: int
    # Rule 6 (Description §10.1): BMI > 25 raises the priority of weight-loss meals.
    prioritise_weight_loss_meals: bool


@dataclass(frozen=True, slots=True)
class BudgetBreakdown:
    """Weekly → daily → per-meal budget (Project Description §10.2)."""

    weekly_inr: Decimal
    daily_inr: Decimal
    per_meal_inr: dict[MealSlot, Decimal]


@dataclass(frozen=True, slots=True)
class MealCandidate:
    """A recipe as seen by the engine, with pre-calculated per-serving values."""

    recipe_id: int
    name: str
    slot: MealSlot
    diet_type: DietType
    prep_time_min: int
    calories_kcal: Decimal
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal
    cost_inr: Decimal
    allergen_ids: frozenset[int] = frozenset()
    food_ids: frozenset[int] = frozenset()


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    candidate: MealCandidate
    score: float


@dataclass(frozen=True, slots=True)
class PlannedSlot:
    """One cell of the plan: either a recipe or an explanation (REQ-4.2.8)."""

    day_of_week: int
    slot: MealSlot
    candidate: MealCandidate | None
    unavailable_reason: str | None = None


@dataclass(frozen=True, slots=True)
class PlanResult:
    slots: tuple[PlannedSlot, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationResult:
    is_valid: bool
    violations: tuple[str, ...] = field(default_factory=tuple)

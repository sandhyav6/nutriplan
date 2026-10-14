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
    """A recipe as seen by the engine: pre-calculated values for ONE serving."""

    recipe_id: int
    name: str
    slot: MealSlot
    category_id: int
    diet_type: DietType
    prep_time_min: int
    calories_kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    sugar_g: float
    fibre_g: float
    cost_inr: Decimal
    allergen_ids: frozenset[int] = frozenset()
    food_ids: frozenset[int] = frozenset()
    # Main (non-pantry) ingredients – used for variety/similarity.
    core_food_ids: frozenset[int] = frozenset()
    has_vegetable: bool = False
    has_fruit: bool = False


@dataclass(frozen=True, slots=True)
class Portion:
    """A candidate scaled to a number of servings (OD-21)."""

    candidate: MealCandidate
    servings: Decimal

    @property
    def calories_kcal(self) -> float:
        return self.candidate.calories_kcal * float(self.servings)

    @property
    def protein_g(self) -> float:
        return self.candidate.protein_g * float(self.servings)

    @property
    def carbs_g(self) -> float:
        return self.candidate.carbs_g * float(self.servings)

    @property
    def fat_g(self) -> float:
        return self.candidate.fat_g * float(self.servings)

    @property
    def sugar_g(self) -> float:
        return self.candidate.sugar_g * float(self.servings)

    @property
    def fibre_g(self) -> float:
        return self.candidate.fibre_g * float(self.servings)

    @property
    def cost_inr(self) -> Decimal:
        return (self.candidate.cost_inr * self.servings).quantize(Decimal("0.01"))


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    portion: Portion
    score: float


@dataclass(frozen=True, slots=True)
class PlannedSlot:
    """One cell of the plan: either a portioned recipe or an explanation (REQ-4.2.8)."""

    day_of_week: int
    slot: MealSlot
    portion: Portion | None
    unavailable_reason: str | None = None


@dataclass(frozen=True, slots=True)
class PlanNote:
    code: str  # e.g. "nutrition", "variety", "unavailable"
    message: str


@dataclass(frozen=True, slots=True)
class PlanResult:
    slots: tuple[PlannedSlot, ...]
    notes: tuple[PlanNote, ...] = ()

    @property
    def total_cost_inr(self) -> Decimal:
        return sum((s.portion.cost_inr for s in self.slots if s.portion), Decimal("0"))

    @property
    def total_calories_kcal(self) -> float:
        return sum(s.portion.calories_kcal for s in self.slots if s.portion)


@dataclass(frozen=True, slots=True)
class Infeasibility:
    """Returned instead of a plan when a hard constraint cannot be met (OD-01)."""

    code: str
    message: str
    minimum_weekly_cost_inr: Decimal | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    is_valid: bool
    violations: tuple[str, ...] = field(default_factory=tuple)

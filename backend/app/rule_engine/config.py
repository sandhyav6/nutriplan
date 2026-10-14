"""Explicit, documented rule-engine configuration (no unexplained magic numbers).

Values marked SOURCE come from the requirements documents. Values marked TBD are
open decisions (docs/requirements/open-decisions.md) and must be agreed before the
milestone that uses them. Values marked DECIDED resolve an open decision.
"""

from typing import Final

from app.models.enums import ActivityLevel, FeedbackType, HealthGoal, MealSlot

# SOURCE: Project Description §8.1 – approximate activity-adjusted calorie baselines (kcal/day).
ACTIVITY_CALORIE_BASELINE: Final[dict[ActivityLevel, int]] = {
    ActivityLevel.SEDENTARY: 1800,
    ActivityLevel.MODERATELY_ACTIVE: 2300,
    ActivityLevel.VERY_ACTIVE: 2800,
}

# SOURCE: Project Description §8.3 – Muscle Gain → protein ≥ 120 g/day, calories ≈ 2600.
MUSCLE_GAIN_MIN_PROTEIN_G: Final[int] = 120
MUSCLE_GAIN_REFERENCE_CALORIES: Final[int] = 2600

# SOURCE: Project Description §8.2 / Rule 6 – BMI above this raises weight-loss meal priority.
BMI_WEIGHT_LOSS_PRIORITY_THRESHOLD: Final[float] = 25.0

# SOURCE: Project Description §10.3 / Lab 2 DFD 5.0 – weighted feedback score.
FEEDBACK_WEIGHTS: Final[dict[FeedbackType, int]] = {
    FeedbackType.FAVOURITE: 3,
    FeedbackType.LIKE: 1,
    FeedbackType.SKIP: -1,
    FeedbackType.DISLIKE: -3,
}

# SOURCE: SRS REQ-4.2.6 – the same meal may appear at most twice in a 7-day plan.
MAX_REPEATS_PER_WEEK: Final[int] = 2

# SOURCE: SRS REQ-4.2.1 – 7 days x breakfast, lunch, dinner, snack.
DAYS_PER_PLAN: Final[int] = 7
MEAL_SLOTS: Final[tuple[MealSlot, ...]] = (
    MealSlot.BREAKFAST,
    MealSlot.LUNCH,
    MealSlot.DINNER,
    MealSlot.SNACK,
)

# DECIDED (OD-05): share of the daily calorie target and daily budget per slot.
SLOT_SHARES: Final[dict[MealSlot, float]] = {
    MealSlot.BREAKFAST: 0.25,
    MealSlot.LUNCH: 0.35,
    MealSlot.DINNER: 0.30,
    MealSlot.SNACK: 0.10,
}

# DECIDED (OD-06): calorie adjustment applied to the activity baseline for each goal.
# Muscle Gain +300 gives 2600 kcal for a moderately active user, matching Description §8.3.
GOAL_CALORIE_ADJUSTMENT_KCAL: Final[dict[HealthGoal, int]] = {
    HealthGoal.WEIGHT_LOSS: -500,
    HealthGoal.MAINTENANCE: 0,
    HealthGoal.MUSCLE_GAIN: 300,
}

# DECIDED (OD-06): weight-loss targets never go below this daily intake.
MIN_DAILY_CALORIES_KCAL: Final[int] = 1200

# DECIDED (OD-06): daily protein target in grams per kg of body weight. Muscle Gain is
# additionally floored at MUSCLE_GAIN_MIN_PROTEIN_G (SOURCE: Description §8.3).
PROTEIN_G_PER_KG: Final[dict[HealthGoal, float]] = {
    HealthGoal.MAINTENANCE: 0.8,
    HealthGoal.WEIGHT_LOSS: 1.2,
    HealthGoal.MUSCLE_GAIN: 1.6,
}

# SOURCE: WHO adult BMI classification (used for display; BMI never gates meals – §8.2).
BMI_CATEGORY_UPPER_BOUNDS: Final[tuple[tuple[float, str], ...]] = (
    (18.5, "underweight"),
    (25.0, "normal"),
    (30.0, "overweight"),
)
BMI_TOP_CATEGORY: Final[str] = "obese"

# DECIDED (OD-07): "acceptable tolerance" for replacement calories (SRS REQ-4.5.4) – ±20 %.
REPLACEMENT_CALORIE_TOLERANCE: Final[float] = 0.20

# DECIDED (OD-08): a candidate more similar than this to the meal served in the same slot the
# previous day is skipped (Description stage 8 / Rule 7).
VARIETY_SIMILARITY_THRESHOLD: Final[float] = 0.80

# DECIDED (OD-21): portion sizes the planner may choose so plans meet the calorie target.
SERVING_STEP: Final[str] = "0.25"
MIN_SERVINGS: Final[str] = "0.75"
MAX_SERVINGS: Final[str] = "2.00"

# DECIDED (OD-03): nutrition fit is soft – a candidate whose portioned calories are within this
# fraction of the slot target counts as a good fit; others are ranked lower, not removed.
NUTRITION_FIT_TOLERANCE: Final[float] = 0.30

# DECIDED (REQ-4.2.7): weekly balance targets – meals containing vegetables / fruit per day.
VEGETABLE_MEALS_PER_DAY: Final[int] = 2
FRUIT_MEALS_PER_DAY: Final[int] = 1

# DECIDED: ranking weights (stage 7). Higher score = better. Documented in architecture overview.
RANKING_WEIGHTS: Final[dict[str, float]] = {
    "nutrition_fit": 3.0,  # closeness to the slot calorie target
    "protein_fit": 1.5,  # protein towards the slot protein target
    "goal_fit": 2.0,  # REQ-4.2.4 goal orientation
    "budget_fit": 1.5,  # cheaper relative to the per-meal budget (Rule 3)
    "over_meal_budget": 1.0,  # penalty when above the per-meal budget
    "feedback": 1.5,  # weighted feedback score / 3 (Rules 5 & 8)
    "favourite_similarity": 1.5,  # Rule 8 – similar to a favourite
    "bmi_priority": 1.0,  # Rule 6 – BMI > 25 favours weight-loss meals
    "repeat_penalty": 1.0,  # per earlier use in the same week
    "recent_penalty": 0.4,  # served in the previous plan
    "balance": 0.3,  # REQ-4.2.7 vegetables / fruit still needed
}

# Food groups ignored when comparing meals for similarity (cooking basics).
PANTRY_FOOD_GROUPS: Final[frozenset[str]] = frozenset(
    {"Oils & Fats", "Spices & Condiments", "Sweeteners"}
)
VEGETABLE_GROUP: Final[str] = "Vegetables"
FRUIT_GROUP: Final[str] = "Fruits"

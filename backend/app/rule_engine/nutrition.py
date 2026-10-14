"""Stage 2 – nutrition profile calculation (Project Description §8).

* BMI = weight_kg / height_m² (§8.2). It is a secondary ranking signal and never gates meals.
* Daily calories = activity baseline (§8.1) + goal adjustment (OD-06), floored for weight loss.
* Daily protein = g/kg for the goal (OD-06); Muscle Gain is at least 120 g/day (§8.3).
* Age and gender are stored but do not change targets (OD-11).

All numbers come from ``config.py``. Functions are pure and deterministic.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.models.enums import HealthGoal, MealSlot
from app.rule_engine import config
from app.rule_engine.types import BudgetBreakdown, NutritionTarget, ProfileInput


def calculate_bmi(weight_kg: Decimal, height_cm: Decimal) -> Decimal:
    """Return BMI = weight_kg / (height_cm / 100)², rounded to one decimal place."""
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be positive.")
    height_m = Decimal(height_cm) / Decimal(100)
    bmi = Decimal(weight_kg) / (height_m * height_m)
    return bmi.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def bmi_category(bmi: Decimal) -> str:
    for upper_bound, label in config.BMI_CATEGORY_UPPER_BOUNDS:
        if bmi < Decimal(str(upper_bound)):
            return label
    return config.BMI_TOP_CATEGORY


def calculate_daily_calories(profile: ProfileInput) -> int:
    baseline = config.ACTIVITY_CALORIE_BASELINE[profile.activity_level]
    target = baseline + config.GOAL_CALORIE_ADJUSTMENT_KCAL[profile.health_goal]
    if profile.health_goal is HealthGoal.WEIGHT_LOSS:
        target = max(target, config.MIN_DAILY_CALORIES_KCAL)
    return target


def calculate_daily_protein(profile: ProfileInput) -> int:
    grams = Decimal(str(config.PROTEIN_G_PER_KG[profile.health_goal])) * Decimal(profile.weight_kg)
    protein = int(grams.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if profile.health_goal is HealthGoal.MUSCLE_GAIN:
        protein = max(protein, config.MUSCLE_GAIN_MIN_PROTEIN_G)
    return protein


def calculate_nutrition_target(profile: ProfileInput) -> NutritionTarget:
    """Resolve activity level and health goal into daily calorie and protein targets."""
    bmi = calculate_bmi(profile.weight_kg, profile.height_cm)
    return NutritionTarget(
        bmi=bmi,
        bmi_category=bmi_category(bmi),
        baseline_calories_kcal=config.ACTIVITY_CALORIE_BASELINE[profile.activity_level],
        daily_calories_kcal=calculate_daily_calories(profile),
        daily_protein_g=calculate_daily_protein(profile),
        prioritise_weight_loss_meals=bmi > Decimal(str(config.BMI_WEIGHT_LOSS_PRIORITY_THRESHOLD)),
    )


def calculate_budget_breakdown(weekly_budget_inr: Decimal) -> BudgetBreakdown:
    """Weekly → daily → per-meal budget (Description §10.2) using ``config.SLOT_SHARES``."""
    weekly = Decimal(weekly_budget_inr)
    daily = weekly / Decimal(config.DAYS_PER_PLAN)
    per_meal = {
        slot: (daily * Decimal(str(share))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        for slot, share in config.SLOT_SHARES.items()
    }
    return BudgetBreakdown(
        weekly_inr=weekly,
        daily_inr=daily.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        per_meal_inr=per_meal,
    )


def slot_targets(target: NutritionTarget) -> dict[MealSlot, tuple[float, float]]:
    """(calories, protein) target for each meal slot."""
    return {
        slot: (target.daily_calories_kcal * share, target.daily_protein_g * share)
        for slot, share in config.SLOT_SHARES.items()
    }

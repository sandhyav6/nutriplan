"""Stages 3–6 – constraint filters.

HARD (never relaxed, OD-03):
* Rule 1 / REQ-4.2.2 – dietary preference           → ``matches_diet``
* Rule 6 (SRS B.3) / REQ-4.2.3 – allergens & foods   → ``is_allergen_free`` (structural id match)
* Rule 4 / REQ-4.2.5 – cooking-time limit            → ``within_cooking_time``
* Weekly budget                                       → enforced by planner + validator
SOFT (preference used to build the first-choice pool and for ranking):
* Rule 3 (Description) – per-meal budget             → ``within_meal_budget``
* Rule 2 / REQ-4.2.4 – goal-based nutrition target   → ``fits_nutrition_target``
"""

from collections.abc import Iterable
from decimal import Decimal

from app.models.enums import DietaryPreference, DietType, HealthGoal, MealSlot
from app.rule_engine import config
from app.rule_engine.types import MealCandidate, Portion, ProfileInput

# A preference allows every diet type at or below its level.
_PREFERENCE_LEVEL = {
    DietaryPreference.VEGAN: 0,
    DietaryPreference.VEGETARIAN: 1,
    DietaryPreference.EGGETARIAN: 2,
    DietaryPreference.NON_VEGETARIAN: 3,
}
_DIET_LEVEL = {
    DietType.VEGAN: 0,
    DietType.VEGETARIAN: 1,
    DietType.EGGETARIAN: 2,
    DietType.NON_VEGETARIAN: 3,
}


def matches_diet(candidate: MealCandidate, profile: ProfileInput) -> bool:
    return _DIET_LEVEL[candidate.diet_type] <= _PREFERENCE_LEVEL[profile.dietary_preference]


def is_allergen_free(candidate: MealCandidate, profile: ProfileInput) -> bool:
    """Safety rule (SRS §5.2): overrides every other rule."""
    return not (candidate.allergen_ids & profile.allergen_ids) and not (
        candidate.food_ids & profile.excluded_food_ids
    )


def within_cooking_time(candidate: MealCandidate, profile: ProfileInput) -> bool:
    return candidate.prep_time_min <= profile.max_cooking_time_min


def passes_hard_constraints(candidate: MealCandidate, profile: ProfileInput) -> bool:
    return (
        matches_diet(candidate, profile)
        and is_allergen_free(candidate, profile)
        and within_cooking_time(candidate, profile)
    )


def within_meal_budget(portion: Portion, per_meal_budget_inr: Decimal) -> bool:
    return portion.cost_inr <= per_meal_budget_inr


def fits_nutrition_target(
    portion: Portion, target_calories: float, target_protein: float, goal: HealthGoal
) -> bool:
    """Goal-oriented nutrition check for one slot (REQ-4.2.4, Rule 2)."""
    tolerance = config.NUTRITION_FIT_TOLERANCE
    calories = portion.calories_kcal
    if abs(calories - target_calories) > target_calories * tolerance:
        return False
    if goal is HealthGoal.WEIGHT_LOSS:
        # calories at or below target, protein above a minimum share of the slot target
        return calories <= target_calories * 1.05 and portion.protein_g >= target_protein * 0.5
    if goal is HealthGoal.MUSCLE_GAIN:
        return portion.protein_g >= target_protein * 0.6
    return True


def eligible_candidates(
    candidates: Iterable[MealCandidate], profile: ProfileInput, slot: MealSlot | None = None
) -> list[MealCandidate]:
    """Every candidate (optionally for one slot) that satisfies all hard constraints."""
    return [
        c
        for c in candidates
        if (slot is None or c.slot == slot) and passes_hard_constraints(c, profile)
    ]


def explain_empty_slot(
    slot: MealSlot, candidates: Iterable[MealCandidate], profile: ProfileInput
) -> str:
    """REQ-4.2.8 – say which constraint removed every option for a slot."""
    label = slot.value
    in_slot = [c for c in candidates if c.slot == slot]
    if not in_slot:
        return f"No {label} recipes exist in the catalogue yet."
    after_diet = [c for c in in_slot if matches_diet(c, profile)]
    if not after_diet:
        return f"No {label} recipe matches your dietary preference."
    after_allergy = [c for c in after_diet if is_allergen_free(c, profile)]
    if not after_allergy:
        return f"Every {label} recipe for your diet contains a declared allergen or excluded food."
    quickest = min(c.prep_time_min for c in after_allergy)
    return (
        f"No safe {label} recipe can be prepared within {profile.max_cooking_time_min} minutes "
        f"(the quickest takes {quickest} min). Increase your cooking time to fill this slot."
    )

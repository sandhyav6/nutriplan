"""Stages 3–6 – hard-constraint filters (never relaxed).

Each rule is a separate predicate so it can be unit-tested in isolation:
* Rule 1 / REQ-4.2.2 – dietary preference
* Rule 6 (SRS B.3) / REQ-4.2.3 – declared allergens and excluded foods (structural id match)
* Rule 4 / REQ-4.2.5 – cooking-time limit
* Rule 3 – per-meal budget
* REQ-4.2.4 – goal-oriented nutrition target filter

Implementation is scheduled for Milestone 2.
"""

from collections.abc import Iterable
from decimal import Decimal

from app.rule_engine.types import MealCandidate, NutritionTarget, ProfileInput

_PENDING = "Scheduled for Milestone 2 (rule engine) – see docs/development-roadmap.md"


def matches_diet(candidate: MealCandidate, profile: ProfileInput) -> bool:
    raise NotImplementedError(_PENDING)


def is_allergen_free(candidate: MealCandidate, profile: ProfileInput) -> bool:
    raise NotImplementedError(_PENDING)


def within_cooking_time(candidate: MealCandidate, profile: ProfileInput) -> bool:
    raise NotImplementedError(_PENDING)


def within_meal_budget(candidate: MealCandidate, per_meal_budget_inr: Decimal) -> bool:
    raise NotImplementedError(_PENDING)


def fits_nutrition_target(candidate: MealCandidate, target: NutritionTarget) -> bool:
    raise NotImplementedError(_PENDING)


def eligible_candidates(
    candidates: Iterable[MealCandidate], profile: ProfileInput
) -> list[MealCandidate]:
    """Apply every hard constraint and return only safe candidates."""
    raise NotImplementedError(_PENDING)

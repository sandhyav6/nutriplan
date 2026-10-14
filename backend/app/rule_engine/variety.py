"""Stage 8 – meal variety (REQ-4.2.6, Rule 7) and similarity used by Rule 8.

* A recipe appears at most ``config.MAX_REPEATS_PER_WEEK`` times per plan (never relaxed –
  OD-17) and never twice on the same day.
* A candidate more similar than ``config.VARIETY_SIMILARITY_THRESHOLD`` to the meal served in
  the same slot the previous day is skipped when an alternative exists.
"""

import math
from collections.abc import Collection, Mapping

from app.rule_engine import config
from app.rule_engine.types import MealCandidate


def ingredient_similarity(a: MealCandidate, b: MealCandidate) -> float:
    """Jaccard overlap of main (non-pantry) ingredients."""
    if not a.core_food_ids and not b.core_food_ids:
        return 0.0
    shared = len(a.core_food_ids & b.core_food_ids)
    return shared / len(a.core_food_ids | b.core_food_ids)


def nutrition_similarity(a: MealCandidate, b: MealCandidate) -> float:
    """Macro-energy profile (cosine) and calorie size closeness, 0..1."""
    va = (a.protein_g * 4, a.carbs_g * 4, a.fat_g * 9)
    vb = (b.protein_g * 4, b.carbs_g * 4, b.fat_g * 9)
    na, nb = math.hypot(*va), math.hypot(*vb)
    cosine = sum(x * y for x, y in zip(va, vb, strict=True)) / (na * nb) if na and nb else 0.0
    biggest = max(a.calories_kcal, b.calories_kcal)
    closeness = 1 - abs(a.calories_kcal - b.calories_kcal) / biggest if biggest else 1.0
    return 0.5 * cosine + 0.5 * closeness


def similarity(a: MealCandidate, b: MealCandidate) -> float:
    """Category / ingredient / nutrition similarity in the range 0..1."""
    if a.recipe_id == b.recipe_id:
        return 1.0
    same_category = 1.0 if a.category_id == b.category_id else 0.0
    return (
        0.5 * ingredient_similarity(a, b) + 0.3 * nutrition_similarity(a, b) + 0.2 * same_category
    )


def favourite_affinity(candidate: MealCandidate, favourites: Collection[MealCandidate]) -> float:
    """Rule 8 – boost (0..1) for meals nutritionally similar to a favourite."""
    best = 0.0
    for fav in favourites:
        if fav.recipe_id == candidate.recipe_id:
            continue
        score = 0.5 * nutrition_similarity(candidate, fav) + 0.5 * ingredient_similarity(
            candidate, fav
        )
        best = max(best, score)
    return max(0.0, (best - 0.5) * 2)


def passes_variety(
    candidate: MealCandidate,
    weekly_counts: Mapping[int, int],
    same_day_ids: Collection[int],
    previous_same_slot: MealCandidate | None = None,
    *,
    strict: bool = True,
) -> bool:
    if weekly_counts.get(candidate.recipe_id, 0) >= config.MAX_REPEATS_PER_WEEK:
        return False
    if candidate.recipe_id in same_day_ids:
        return False
    if strict and previous_same_slot is not None:
        if previous_same_slot.recipe_id == candidate.recipe_id:
            return False
        if similarity(previous_same_slot, candidate) > config.VARIETY_SIMILARITY_THRESHOLD:
            return False
    return True

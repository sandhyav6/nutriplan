"""Unit tests for the deterministic rule engine (SRS §4.2, §4.5, Appendix B; §5.4)."""

from collections import Counter
from dataclasses import replace
from decimal import Decimal

import pytest

from app.models.enums import ActivityLevel, DietaryPreference, DietType, HealthGoal, MealSlot
from app.rule_engine import config, filters, variety
from app.rule_engine.nutrition import calculate_nutrition_target
from app.rule_engine.planner import (
    PlannerInput,
    choose_servings,
    find_replacement,
    generate_weekly_plan,
)
from app.rule_engine.ranking import RankingContext, rank_portions
from app.rule_engine.types import (
    Infeasibility,
    MealCandidate,
    PlannedSlot,
    PlanResult,
    Portion,
    ProfileInput,
)
from app.rule_engine.validator import validate_plan

PEANUT, DAIRY = 1, 3
CATEGORY = {MealSlot.BREAKFAST: 1, MealSlot.LUNCH: 2, MealSlot.DINNER: 3, MealSlot.SNACK: 4}
SLOT_KCAL = {
    MealSlot.BREAKFAST: 500,
    MealSlot.LUNCH: 700,
    MealSlot.DINNER: 600,
    MealSlot.SNACK: 200,
}


def meal(
    rid: int,
    slot: MealSlot,
    *,
    diet=DietType.VEGAN,
    time=15,
    cost="30",
    allergens=(),
    foods=None,
    kcal=None,
    protein=20.0,
):  # type: ignore[no-untyped-def]
    foods = foods if foods is not None else {1000 + rid}
    return MealCandidate(
        recipe_id=rid,
        name=f"Meal {rid}",
        slot=slot,
        category_id=CATEGORY[slot],
        diet_type=diet,
        prep_time_min=time,
        calories_kcal=float(kcal or SLOT_KCAL[slot]),
        protein_g=protein,
        carbs_g=60.0,
        fat_g=15.0,
        sugar_g=5.0,
        fibre_g=6.0,
        cost_inr=Decimal(cost),
        allergen_ids=frozenset(allergens),
        food_ids=frozenset(foods),
        core_food_ids=frozenset(foods),
        has_vegetable=rid % 2 == 0,
        has_fruit=rid % 3 == 0,
    )


def catalogue(per_slot: int = 6) -> list[MealCandidate]:
    items = []
    for s_index, slot in enumerate(config.MEAL_SLOTS):
        for i in range(per_slot):
            items.append(meal(s_index * 100 + i + 1, slot, cost=str(20 + i * 5)))
    return items


def profile(**kw) -> ProfileInput:  # type: ignore[no-untyped-def]
    base = {
        "age": 22,
        "height_cm": Decimal("165"),
        "weight_kg": Decimal("60"),
        "activity_level": ActivityLevel.MODERATELY_ACTIVE,
        "dietary_preference": DietaryPreference.VEGETARIAN,
        "health_goal": HealthGoal.MAINTENANCE,
        "weekly_budget_inr": Decimal("3000"),
        "max_cooking_time_min": 30,
    }
    return ProfileInput(**{**base, **kw})


def plan_for(p: ProfileInput, candidates: list[MealCandidate], **kw) -> PlanResult | Infeasibility:  # type: ignore[no-untyped-def]
    return generate_weekly_plan(PlannerInput(p, calculate_nutrition_target(p), candidates, **kw))


# ------------------------------------------------------------- hard filters
def test_diet_rule_vegetarian_excludes_egg_and_meat() -> None:  # Rule 1 / REQ-4.2.2
    p = profile(dietary_preference=DietaryPreference.VEGETARIAN)
    assert filters.matches_diet(meal(1, MealSlot.LUNCH, diet=DietType.VEGETARIAN), p)
    assert not filters.matches_diet(meal(2, MealSlot.LUNCH, diet=DietType.EGGETARIAN), p)
    assert not filters.matches_diet(meal(3, MealSlot.LUNCH, diet=DietType.NON_VEGETARIAN), p)
    vegan = profile(dietary_preference=DietaryPreference.VEGAN)
    assert not filters.matches_diet(meal(4, MealSlot.LUNCH, diet=DietType.VEGETARIAN), vegan)


def test_allergy_rule_uses_allergen_ids_and_excluded_foods() -> None:  # REQ-4.2.3
    p = profile(allergen_ids=frozenset({PEANUT}), excluded_food_ids=frozenset({77}))
    assert not filters.is_allergen_free(meal(1, MealSlot.SNACK, allergens={PEANUT}), p)
    assert not filters.is_allergen_free(meal(2, MealSlot.SNACK, foods={77, 78}), p)
    assert filters.is_allergen_free(meal(3, MealSlot.SNACK, allergens={DAIRY}), p)


def test_cooking_time_boundary() -> None:  # Rule 4 / REQ-4.2.5
    p = profile(max_cooking_time_min=20)
    assert filters.within_cooking_time(meal(1, MealSlot.LUNCH, time=20), p)
    assert not filters.within_cooking_time(meal(2, MealSlot.LUNCH, time=21), p)


def test_explain_empty_slot_names_the_constraint() -> None:  # REQ-4.2.8
    p = profile(max_cooking_time_min=10)
    reason = filters.explain_empty_slot(MealSlot.LUNCH, [meal(1, MealSlot.LUNCH, time=25)], p)
    assert "10 minutes" in reason and "25 min" in reason


# --------------------------------------------------------------- portions
def test_choose_servings_steps_and_limits() -> None:
    c = meal(1, MealSlot.LUNCH, kcal=400)
    assert choose_servings(c, 600) == Decimal("1.50")
    assert choose_servings(c, 100) == Decimal("0.75")
    assert choose_servings(c, 5000) == Decimal("2.00")


# --------------------------------------------------------------- planner
def test_plan_has_seven_days_four_slots_and_is_valid() -> None:  # REQ-4.2.1
    p = profile()
    result = plan_for(p, catalogue())
    assert isinstance(result, PlanResult)
    assert len(result.slots) == 28
    assert {(s.day_of_week, s.slot) for s in result.slots} == {
        (d, s) for d in range(7) for s in config.MEAL_SLOTS
    }
    assert all(s.portion for s in result.slots)
    assert validate_plan(result, p).is_valid


def test_plan_never_repeats_a_meal_more_than_twice() -> None:  # REQ-4.2.6 / Rule 7
    result = plan_for(profile(), catalogue(per_slot=4))
    counts = Counter(s.portion.candidate.recipe_id for s in result.slots if s.portion)
    assert max(counts.values()) <= config.MAX_REPEATS_PER_WEEK


def test_too_few_meals_leaves_explained_slots_instead_of_breaking_repeat_limit() -> None:
    result = plan_for(profile(), catalogue(per_slot=2))  # 2 meals x 2 repeats = 4 of 7 days
    lunches = [s for s in result.slots if s.slot is MealSlot.LUNCH]
    assert sum(1 for s in lunches if s.portion) == 4
    assert all(s.unavailable_reason for s in lunches if not s.portion)
    assert any(n.code == "variety" for n in result.notes)


def test_hard_constraints_are_never_relaxed() -> None:
    p = profile(allergen_ids=frozenset({PEANUT}), max_cooking_time_min=20)
    unsafe = [meal(900 + i, MealSlot.DINNER, allergens={PEANUT}, cost="5") for i in range(5)]
    slow = [meal(950 + i, MealSlot.DINNER, time=45, cost="5") for i in range(5)]
    meat = [
        meal(980 + i, MealSlot.DINNER, diet=DietType.NON_VEGETARIAN, cost="5") for i in range(5)
    ]
    result = plan_for(p, catalogue() + unsafe + slow + meat)
    used = {s.portion.candidate.recipe_id for s in result.slots if s.portion}
    assert used.isdisjoint({c.recipe_id for c in unsafe + slow + meat})
    assert validate_plan(result, p).is_valid


def test_empty_slot_when_no_safe_meal_exists() -> None:  # REQ-4.2.8
    candidates = [c for c in catalogue() if c.slot is not MealSlot.BREAKFAST]
    result = plan_for(profile(), candidates)
    breakfasts = [s for s in result.slots if s.slot is MealSlot.BREAKFAST]
    assert all(s.portion is None and s.unavailable_reason for s in breakfasts)
    assert any(n.code == "unavailable" for n in result.notes)


def test_weekly_budget_enforced_or_infeasible() -> None:  # Rule 3, OD-01
    candidates = catalogue()
    tight = profile(weekly_budget_inr=Decimal("700"))
    result = plan_for(tight, candidates)
    if isinstance(result, PlanResult):
        assert result.total_cost_inr <= Decimal("700")
    impossible = plan_for(profile(weekly_budget_inr=Decimal("100")), candidates)
    assert isinstance(impossible, Infeasibility)
    assert impossible.code == "budget_infeasible"
    assert impossible.minimum_weekly_cost_inr and impossible.minimum_weekly_cost_inr > 100


def test_plan_is_deterministic() -> None:  # SRS §5.4 Reliability
    p = profile()
    assert plan_for(p, catalogue()) == plan_for(p, catalogue())


def test_plan_meets_calorie_target_approximately() -> None:
    p = profile()
    result = plan_for(p, catalogue())
    target = calculate_nutrition_target(p).daily_calories_kcal
    average = result.total_calories_kcal / 7
    assert abs(average - target) <= target * 0.15


# ------------------------------------------------------- ranking & feedback
def ctx(**kw) -> RankingContext:  # type: ignore[no-untyped-def]
    base = {
        "goal": HealthGoal.MAINTENANCE,
        "calorie_target": 700.0,
        "protein_target": 20.0,
        "sugar_limit": 20.0,
        "per_meal_budget_inr": Decimal("60"),
    }
    return RankingContext(**{**base, **kw})


def test_feedback_changes_ranking() -> None:  # REQ-4.4.3 / REQ-4.4.4
    a, b = meal(1, MealSlot.LUNCH), meal(2, MealSlot.LUNCH)
    portions = [Portion(a, Decimal("1")), Portion(b, Decimal("1"))]
    assert rank_portions(portions, ctx())[0].portion.candidate.recipe_id == 1  # tie → lowest id
    disliked = rank_portions(portions, ctx(feedback_scores={1: -3}))
    assert disliked[0].portion.candidate.recipe_id == 2
    liked = rank_portions(portions, ctx(feedback_scores={2: 3}))
    assert liked[0].portion.candidate.recipe_id == 2


def test_goal_orientation_changes_ranking() -> None:  # REQ-4.2.4
    light = replace(
        meal(1, MealSlot.LUNCH, kcal=500, protein=35.0), sugar_g=3.0, fibre_g=2.0
    )  # low-calorie, high-protein, low-sugar
    hearty = replace(
        meal(2, MealSlot.LUNCH, kcal=750, protein=30.0), sugar_g=12.0, fibre_g=10.0
    )  # higher-calorie, complex carbs
    portions = [Portion(light, Decimal("1")), Portion(hearty, Decimal("1"))]
    goal_ctx = {"protein_target": 30.0}
    weight_loss = rank_portions(portions, ctx(goal=HealthGoal.WEIGHT_LOSS, **goal_ctx))
    assert weight_loss[0].portion.candidate.recipe_id == 1
    muscle_gain = rank_portions(portions, ctx(goal=HealthGoal.MUSCLE_GAIN, **goal_ctx))
    assert muscle_gain[0].portion.candidate.recipe_id == 2


def test_weekly_balance_favours_vegetables_and_fruit() -> None:  # REQ-4.2.7
    plain, with_veg = meal(1, MealSlot.LUNCH), meal(3, MealSlot.LUNCH)
    plain = replace(plain, has_vegetable=False, has_fruit=False)
    with_veg = replace(with_veg, has_vegetable=True, has_fruit=False)
    portions = [Portion(plain, Decimal("1")), Portion(with_veg, Decimal("1"))]
    assert rank_portions(portions, ctx())[0].portion.candidate.recipe_id == 1  # tie → lowest id
    assert rank_portions(portions, ctx(need_vegetable=True))[0].portion.candidate.recipe_id == 3

    result = plan_for(profile(), catalogue())
    filled = [s.portion.candidate for s in result.slots if s.portion]
    days = config.DAYS_PER_PLAN
    assert sum(c.has_vegetable for c in filled) >= config.VEGETABLE_MEALS_PER_DAY * days
    assert sum(c.has_fruit for c in filled) >= config.FRUIT_MEALS_PER_DAY * days


def test_favourite_boosts_similar_meals() -> None:  # Rule 8
    favourite = meal(1, MealSlot.DINNER, foods={10, 11, 12})
    similar = meal(2, MealSlot.LUNCH, foods={10, 11, 13})
    different = meal(3, MealSlot.LUNCH, foods={20, 21, 22})
    assert variety.favourite_affinity(similar, [favourite]) > variety.favourite_affinity(
        different, [favourite]
    )
    ranked = rank_portions(
        [Portion(different, Decimal("1")), Portion(similar, Decimal("1"))],
        ctx(favourites=[favourite]),
    )
    assert ranked[0].portion.candidate.recipe_id == 2


def test_variety_blocks_repeats_and_near_duplicates() -> None:
    a = meal(1, MealSlot.LUNCH, foods={1, 2, 3})
    near = meal(2, MealSlot.LUNCH, foods={1, 2, 3})
    assert not variety.passes_variety(a, {1: 2}, set())
    assert not variety.passes_variety(a, {}, {1})
    assert not variety.passes_variety(near, {}, set(), previous_same_slot=a)
    assert variety.passes_variety(near, {}, set(), previous_same_slot=a, strict=False)


# ------------------------------------------------------------- replacement
def test_replacement_keeps_constraints_and_calorie_tolerance() -> None:  # REQ-4.5.x
    p = profile(allergen_ids=frozenset({PEANUT}))
    candidates = [*catalogue(), meal(999, MealSlot.LUNCH, allergens={PEANUT}, cost="1")]
    inp = PlannerInput(p, calculate_nutrition_target(p), candidates)
    plan = generate_weekly_plan(inp)
    index = next(i for i, s in enumerate(plan.slots) if s.slot is MealSlot.LUNCH)
    original = plan.slots[index].portion
    result = find_replacement(inp, list(plan.slots), index)
    assert result.portion is not None
    new = result.portion
    assert new.candidate.recipe_id not in (original.candidate.recipe_id, 999)
    assert abs(new.calories_kcal - original.calories_kcal) <= original.calories_kcal * 0.2
    slots = list(plan.slots)
    slots[index] = PlannedSlot(slots[index].day_of_week, MealSlot.LUNCH, new)
    assert validate_plan(PlanResult(tuple(slots)), p).is_valid


def test_replacement_reports_when_none_exists() -> None:  # REQ-4.5.5
    p = profile()
    candidates = catalogue(per_slot=1)
    inp = PlannerInput(p, calculate_nutrition_target(p), candidates)
    plan = generate_weekly_plan(inp)
    index = next(i for i, s in enumerate(plan.slots) if s.portion)
    result = find_replacement(inp, list(plan.slots), index)
    assert result.portion is None
    assert "current meal has been kept" in result.reason


# ---------------------------------------------------------------- validator
@pytest.mark.parametrize(
    ("override", "fragment"),
    [
        ({"diet": DietType.NON_VEGETARIAN}, "dietary preference"),
        ({"allergens": {PEANUT}}, "allergen"),
        ({"time": 90}, "cooking-time"),
    ],
)
def test_validator_catches_violations(override: dict, fragment: str) -> None:  # type: ignore[type-arg]
    p = profile(allergen_ids=frozenset({PEANUT}))
    bad = Portion(meal(1, MealSlot.LUNCH, **override), Decimal("1"))
    result = validate_plan(PlanResult((PlannedSlot(0, MealSlot.LUNCH, bad),)), p)
    assert not result.is_valid
    assert any(fragment in v for v in result.violations)


def test_validator_catches_budget_and_repeats() -> None:
    p = profile(weekly_budget_inr=Decimal("50"))
    portion = Portion(meal(1, MealSlot.LUNCH, cost="30"), Decimal("1"))
    slots = tuple(PlannedSlot(d, MealSlot.LUNCH, portion) for d in range(3))
    result = validate_plan(PlanResult(slots), p)
    assert any("exceeds budget" in v for v in result.violations)
    assert any("appears 3 times" in v for v in result.violations)

"""Project Description §8 – nutrition profile calculation (OD-06, OD-11)."""

from decimal import Decimal

import pytest

from app.models.enums import ActivityLevel, DietaryPreference, HealthGoal
from app.rule_engine.nutrition import (
    bmi_category,
    calculate_bmi,
    calculate_budget_breakdown,
    calculate_nutrition_target,
)
from app.rule_engine.types import ProfileInput


def profile(**kw) -> ProfileInput:  # type: ignore[no-untyped-def]
    base = {
        "age": 25,
        "height_cm": Decimal("170"),
        "weight_kg": Decimal("65"),
        "activity_level": ActivityLevel.MODERATELY_ACTIVE,
        "dietary_preference": DietaryPreference.VEGETARIAN,
        "health_goal": HealthGoal.MAINTENANCE,
        "weekly_budget_inr": Decimal("1400"),
        "max_cooking_time_min": 30,
    }
    return ProfileInput(**{**base, **kw})


def test_bmi_formula() -> None:
    assert calculate_bmi(Decimal("65"), Decimal("170")) == Decimal("22.5")
    assert calculate_bmi(Decimal("90"), Decimal("175")) == Decimal("29.4")
    with pytest.raises(ValueError):
        calculate_bmi(Decimal("0"), Decimal("170"))


@pytest.mark.parametrize(
    ("bmi", "label"),
    [
        ("18.4", "underweight"),
        ("18.5", "normal"),
        ("24.9", "normal"),
        ("25", "overweight"),
        ("30", "obese"),
    ],
)
def test_bmi_categories(bmi: str, label: str) -> None:
    assert bmi_category(Decimal(bmi)) == label


@pytest.mark.parametrize(
    ("activity", "goal", "calories"),
    [
        (ActivityLevel.SEDENTARY, HealthGoal.MAINTENANCE, 1800),
        (ActivityLevel.MODERATELY_ACTIVE, HealthGoal.MAINTENANCE, 2300),
        (ActivityLevel.VERY_ACTIVE, HealthGoal.MAINTENANCE, 2800),
        (ActivityLevel.MODERATELY_ACTIVE, HealthGoal.MUSCLE_GAIN, 2600),  # §8.3 ≈ 2600
        (ActivityLevel.MODERATELY_ACTIVE, HealthGoal.WEIGHT_LOSS, 1800),
        (ActivityLevel.SEDENTARY, HealthGoal.WEIGHT_LOSS, 1300),
    ],
)
def test_calorie_targets(activity: ActivityLevel, goal: HealthGoal, calories: int) -> None:
    target = calculate_nutrition_target(profile(activity_level=activity, health_goal=goal))
    assert target.daily_calories_kcal == calories


def test_weight_loss_floor_and_protein_targets() -> None:
    assert (
        calculate_nutrition_target(profile(health_goal=HealthGoal.MAINTENANCE)).daily_protein_g
        == 52
    )
    assert (
        calculate_nutrition_target(profile(health_goal=HealthGoal.WEIGHT_LOSS)).daily_protein_g
        == 78
    )
    # Muscle Gain: 1.6 g/kg but never below 120 g/day (§8.3)
    assert (
        calculate_nutrition_target(profile(health_goal=HealthGoal.MUSCLE_GAIN)).daily_protein_g
        == 120
    )
    heavy = profile(health_goal=HealthGoal.MUSCLE_GAIN, weight_kg=Decimal("90"))
    assert calculate_nutrition_target(heavy).daily_protein_g == 144


def test_age_and_gender_do_not_change_targets() -> None:  # OD-11
    assert calculate_nutrition_target(profile(age=18)) == calculate_nutrition_target(
        profile(age=60)
    )


def test_bmi_over_25_raises_weight_loss_priority() -> None:
    assert calculate_nutrition_target(profile(weight_kg=Decimal("80"))).prioritise_weight_loss_meals
    assert not calculate_nutrition_target(profile()).prioritise_weight_loss_meals


def test_budget_breakdown() -> None:
    budget = calculate_budget_breakdown(Decimal("1400"))
    assert budget.daily_inr == Decimal("200.00")
    assert sum(budget.per_meal_inr.values()) == Decimal("200.00")

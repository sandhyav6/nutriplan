"""Milestone 0: the rule engine exists structurally; algorithms are explicitly pending."""

import importlib

import pytest

from app.models.enums import ActivityLevel, FeedbackType
from app.rule_engine import config

MODULES = ["nutrition", "filters", "ranking", "variety", "planner", "validator", "types", "config"]


@pytest.mark.parametrize("name", MODULES)
def test_rule_engine_modules_import(name: str) -> None:
    importlib.import_module(f"app.rule_engine.{name}")


def test_rule_engine_does_not_depend_on_api_or_db_session() -> None:
    for name in MODULES:
        source = importlib.import_module(f"app.rule_engine.{name}").__loader__.get_source(  # type: ignore[union-attr]
            f"app.rule_engine.{name}"
        )
        assert "app.api" not in source
        assert "app.db.session" not in source
        assert "fastapi" not in source


def test_documented_constants_match_requirements() -> None:
    assert config.FEEDBACK_WEIGHTS == {
        FeedbackType.FAVOURITE: 3,
        FeedbackType.LIKE: 1,
        FeedbackType.SKIP: -1,
        FeedbackType.DISLIKE: -3,
    }
    assert config.ACTIVITY_CALORIE_BASELINE[ActivityLevel.SEDENTARY] == 1800
    assert config.ACTIVITY_CALORIE_BASELINE[ActivityLevel.MODERATELY_ACTIVE] == 2300
    assert config.ACTIVITY_CALORIE_BASELINE[ActivityLevel.VERY_ACTIVE] == 2800
    assert config.MAX_REPEATS_PER_WEEK == 2
    assert config.MUSCLE_GAIN_MIN_PROTEIN_G == 120
    assert len(config.MEAL_SLOTS) == 4

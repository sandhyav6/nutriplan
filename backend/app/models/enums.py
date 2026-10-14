"""Domain enumerations (stored as VARCHAR + CHECK constraints, not native PG enums)."""

from enum import StrEnum

from sqlalchemy import Enum as SAEnum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ActivityLevel(StrEnum):
    """Project Description §8.1 – activity scales the baseline calorie estimate."""

    SEDENTARY = "sedentary"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"


class DietaryPreference(StrEnum):
    """What the user is willing to eat (ordered from most to least restrictive)."""

    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    EGGETARIAN = "eggetarian"
    NON_VEGETARIAN = "non_vegetarian"


class DietType(StrEnum):
    """Diet classification of a food; a recipe's diet type derives from its ingredients."""

    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    EGGETARIAN = "eggetarian"
    NON_VEGETARIAN = "non_vegetarian"


class HealthGoal(StrEnum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"


class MealSlot(StrEnum):
    """The four fixed meal categories (SRS Appendix A – Meal Category)."""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class MeasurementUnit(StrEnum):
    """Canonical base units – every quantity is stored in one of these."""

    GRAM = "g"
    MILLILITRE = "ml"
    PIECE = "piece"


class MealPlanStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class FeedbackType(StrEnum):
    """Weights live in app.rule_engine.config.FEEDBACK_WEIGHTS."""

    FAVOURITE = "favourite"
    LIKE = "like"
    SKIP = "skip"
    DISLIKE = "dislike"


def enum_column(enum_cls: type[StrEnum], name: str) -> SAEnum:
    """VARCHAR column restricted by a named CHECK constraint to the enum's values."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=max(len(member.value) for member in enum_cls),
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )

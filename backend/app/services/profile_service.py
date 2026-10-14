"""Profile management (UC-04 Create Profile, UC-05 Update Profile) and nutrition profile."""

from dataclasses import asdict

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import User, UserProfile
from app.repositories import profiles as profile_repo
from app.rule_engine.nutrition import calculate_nutrition_target
from app.rule_engine.types import NutritionTarget, ProfileInput
from app.schemas.profile import NamedRef, NutritionTargetOut, ProfileIn, ProfileOut


def to_profile_input(profile: UserProfile) -> ProfileInput:
    return ProfileInput(
        age=profile.age,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        activity_level=profile.activity_level,
        dietary_preference=profile.dietary_preference,
        health_goal=profile.health_goal,
        weekly_budget_inr=profile.weekly_budget_inr,
        max_cooking_time_min=profile.max_cooking_time_min,
        allergen_ids=frozenset(a.id for a in profile.allergens),
        excluded_food_ids=frozenset(f.id for f in profile.excluded_foods),
    )


def nutrition_for(profile: UserProfile) -> NutritionTarget:
    return calculate_nutrition_target(to_profile_input(profile))


def to_profile_out(profile: UserProfile) -> ProfileOut:
    return ProfileOut(
        id=profile.id,
        age=profile.age,
        gender=profile.gender,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        activity_level=profile.activity_level,
        dietary_preference=profile.dietary_preference,
        health_goal=profile.health_goal,
        weekly_budget_inr=profile.weekly_budget_inr,
        max_cooking_time_min=profile.max_cooking_time_min,
        allergens=[
            NamedRef.model_validate(a) for a in sorted(profile.allergens, key=lambda a: a.name)
        ],
        excluded_foods=[
            NamedRef.model_validate(f) for f in sorted(profile.excluded_foods, key=lambda f: f.name)
        ],
        updated_at=profile.updated_at,
        nutrition=NutritionTargetOut(**asdict(nutrition_for(profile))),
    )


def get_profile(db: Session, user: User) -> UserProfile:
    profile = profile_repo.get_for_user(db, user.id)
    if profile is None:
        raise AppError(404, "profile_not_found", "You have not created a profile yet.")
    return profile


def save_profile(db: Session, user: User, data: ProfileIn) -> tuple[UserProfile, bool]:
    """Create or replace the user's profile. Returns (profile, created)."""
    allergens = profile_repo.get_allergens(db, data.allergen_ids)
    if len(allergens) != len(data.allergen_ids):
        raise AppError(
            422,
            "validation_error",
            "One or more selected allergens do not exist.",
            [{"location": ["body", "allergen_ids"], "message": "Unknown allergen."}],
        )
    foods = profile_repo.get_foods(db, data.excluded_food_ids)
    if len(foods) != len(data.excluded_food_ids):
        raise AppError(
            422,
            "validation_error",
            "One or more excluded foods do not exist.",
            [{"location": ["body", "excluded_food_ids"], "message": "Unknown food."}],
        )

    profile = profile_repo.get_for_user(db, user.id)
    created = profile is None
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    fields = data.model_dump(exclude={"allergen_ids", "excluded_food_ids"})
    for key, value in fields.items():
        setattr(profile, key, value)
    profile.allergens = allergens
    profile.excluded_foods = foods
    db.commit()
    db.refresh(profile)
    return profile, created

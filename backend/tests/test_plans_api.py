"""End-to-end API flow: profile → plan → grocery list → feedback → replacement → dashboard."""

from collections import Counter
from decimal import Decimal
from time import perf_counter

from sqlalchemy import select

from app.models import Feedback, User
from app.models.enums import FeedbackType, MeasurementUnit
from app.services.grocery_service import display_quantity
from tests.conftest import VALID_PROFILE


def _user_with_plan(api, **profile):  # type: ignore[no-untyped-def]
    api.register()
    assert api.put("/profile", {**VALID_PROFILE, **profile}).status_code == 201
    response = api.post("/meal-plans/generate")
    assert response.status_code == 201, response.text
    return response.json()


def test_generate_requires_profile(api, seeded) -> None:  # type: ignore[no-untyped-def]
    api.register()
    response = api.post("/meal-plans/generate")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "profile_required"


def test_generate_with_empty_catalogue(api) -> None:  # type: ignore[no-untyped-def]
    api.register()
    api.put("/profile", VALID_PROFILE)
    assert api.post("/meal-plans/generate").json()["error"]["code"] == "catalogue_empty"


def test_generate_plan_respects_constraints(api, seeded) -> None:  # type: ignore[no-untyped-def]
    allergens = {a["name"]: a["id"] for a in api.get("/allergens").json()}
    plan = _user_with_plan(api, allergen_ids=[allergens["Peanuts"]], max_cooking_time_min=20)
    meals = plan["meals"]
    assert len(meals) == 28
    filled = [m for m in meals if m["meal"]]
    assert all(m["meal"]["prep_time_min"] <= 20 for m in filled)
    assert all(m["meal"]["diet_type"] in ("vegan", "vegetarian") for m in filled)
    assert max(Counter(m["meal"]["recipe_id"] for m in filled).values()) <= 2
    assert all(m["unavailable_reason"] for m in meals if not m["meal"])
    assert Decimal(plan["total_cost_inr"]) <= Decimal(VALID_PROFILE["weekly_budget_inr"])
    for m in filled:
        detail = api.get(f"/meal-plans/current/meals/{m['id']}").json()
        assert "Peanuts" not in detail["allergens"]
    assert api.get("/meal-plans/current").json()["id"] == plan["id"]


def test_infeasible_budget_returns_explanation(api, seeded) -> None:  # type: ignore[no-untyped-def]
    api.register()
    api.put("/profile", {**VALID_PROFILE, "weekly_budget_inr": "100"})
    response = api.post("/meal-plans/generate")
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "budget_infeasible"
    assert Decimal(error["details"]["minimum_weekly_cost_inr"]) > 100
    assert api.get("/meal-plans/current").status_code == 404  # nothing unsafe was saved


def test_grocery_list_aggregates_plan_ingredients(api, seeded) -> None:  # type: ignore[no-untyped-def]
    _user_with_plan(api)
    grocery = api.get("/grocery-lists/current")
    assert grocery.status_code == 200
    body = grocery.json()
    names = [i["name"] for g in body["groups"] for i in g["items"]]
    assert len(names) == len(set(names)) == body["item_count"]  # de-duplicated (REQ-4.3.2)
    total = sum(Decimal(i["estimated_cost_inr"]) for g in body["groups"] for i in g["items"])
    assert total == Decimal(body["total_estimated_cost_inr"])
    assert all(i["display_quantity"] for g in body["groups"] for i in g["items"])


def test_display_units() -> None:  # REQ-4.3.4
    assert display_quantity(Decimal("500"), MeasurementUnit.GRAM) == "500 g"
    assert display_quantity(Decimal("11.25"), MeasurementUnit.GRAM) == "11 g"
    assert display_quantity(Decimal("0.4"), MeasurementUnit.MILLILITRE) == "1 ml"
    assert display_quantity(Decimal("1250"), MeasurementUnit.GRAM) == "1.25 kg"
    assert display_quantity(Decimal("2000"), MeasurementUnit.MILLILITRE) == "2 L"
    assert display_quantity(Decimal("2.5"), MeasurementUnit.PIECE) == "3 pieces"
    assert display_quantity(Decimal("1"), MeasurementUnit.PIECE) == "1 piece"


def test_feedback_and_dashboard(api, seeded) -> None:  # type: ignore[no-untyped-def]
    plan = _user_with_plan(api)
    filled = [m for m in plan["meals"] if m["meal"]]
    first, second = filled[0], filled[1]
    assert (
        api.post(
            "/feedback", {"planned_meal_id": first["id"], "feedback_type": "favourite"}
        ).status_code
        == 201
    )
    response = api.post("/feedback", {"planned_meal_id": second["id"], "feedback_type": "dislike"})
    assert response.status_code == 201 and response.json()["score"] == -3
    assert (
        api.post(
            "/feedback", {"planned_meal_id": first["id"], "feedback_type": "bogus"}
        ).status_code
        == 422
    )

    # REQ-4.4.2: each event stores the user, meal, feedback type and a timestamp.
    stored = seeded.scalars(select(Feedback).order_by(Feedback.id)).all()
    user_id = seeded.scalar(select(User.id).where(User.email == "asha@example.com"))
    assert [(f.user_id, f.recipe_id, f.feedback_type) for f in stored] == [
        (user_id, first["meal"]["recipe_id"], FeedbackType.FAVOURITE),
        (user_id, second["meal"]["recipe_id"], FeedbackType.DISLIKE),
    ]
    assert all(f.created_at is not None for f in stored)

    current = {m["id"]: m for m in api.get("/meal-plans/current").json()["meals"]}
    assert current[first["id"]]["feedback"] == "favourite"
    assert current[second["id"]]["feedback"] == "dislike"

    dash = api.get("/dashboard").json()
    assert dash["has_plan"] is True
    assert Decimal(dash["total_calories_kcal"]) > 0
    assert Decimal(dash["estimated_spend_inr"]) > 0
    assert sum(dash["meals_by_slot"].values()) == len(filled)
    assert dash["feedback_on_plan"]["favourite"] == 1
    assert dash["feedback_on_plan"]["dislike"] == 1
    assert [f["recipe_id"] for f in dash["favourites"]] == [first["meal"]["recipe_id"]]
    assert len(dash["days"]) == 7


def test_feedback_is_private(make_api, seeded) -> None:  # type: ignore[no-untyped-def]
    owner, other = make_api(), make_api()
    plan = _user_with_plan(owner)
    meal_id = next(m["id"] for m in plan["meals"] if m["meal"])
    other.register(email="other@example.com")
    response = other.post("/feedback", {"planned_meal_id": meal_id, "feedback_type": "like"})
    assert response.status_code == 404
    assert other.get(f"/meal-plans/current/meals/{meal_id}").status_code == 404


def test_replace_meal_updates_plan_and_grocery_list(api, seeded) -> None:  # type: ignore[no-untyped-def]
    plan = _user_with_plan(api)
    target = next(m for m in plan["meals"] if m["meal"] and m["slot"] == "lunch")
    before_grocery = api.get("/grocery-lists/current").json()
    response = api.post(f"/meal-plans/current/meals/{target['id']}/replace")
    assert response.status_code == 200, response.text
    new_meal = response.json()["meal"]["meal"]
    assert new_meal["recipe_id"] != target["meal"]["recipe_id"]
    old_kcal = Decimal(target["meal"]["calories_kcal"])
    assert abs(Decimal(new_meal["calories_kcal"]) - old_kcal) <= old_kcal * Decimal("0.2") + 1
    after = api.get("/meal-plans/current").json()
    assert Decimal(after["total_cost_inr"]) <= Decimal(VALID_PROFILE["weekly_budget_inr"])
    assert max(Counter(m["meal"]["recipe_id"] for m in after["meals"] if m["meal"]).values()) <= 2
    after_grocery = api.get("/grocery-lists/current").json()
    grocery_names = {i["name"] for g in after_grocery["groups"] for i in g["items"]}
    new_ingredients = {i["name"] for i in response.json()["meal"]["ingredients"]}
    assert new_ingredients <= grocery_names  # regenerated with the new meal (REQ-4.3.3)
    # Grocery total tracks the plan again after the swap.
    plan_cost = Decimal(after["total_cost_inr"])
    grocery_cost = Decimal(after_grocery["total_estimated_cost_inr"])
    assert abs(plan_cost - grocery_cost) <= Decimal("5")
    assert grocery_cost != Decimal(
        before_grocery["total_estimated_cost_inr"]
    ) or plan_cost == Decimal(plan["total_cost_inr"])


def test_regenerating_archives_previous_plan(api, seeded) -> None:  # type: ignore[no-untyped-def]
    first = _user_with_plan(api)
    second = api.post("/meal-plans/generate").json()
    assert second["id"] != first["id"]
    assert api.get("/meal-plans/current").json()["id"] == second["id"]


def test_dashboard_without_plan(api) -> None:  # type: ignore[no-untyped-def]
    api.register()
    dash = api.get("/dashboard").json()
    assert dash["has_plan"] is False and dash["nutrition"] is None


def test_repeated_replacement_does_not_bounce_back(api, seeded) -> None:  # type: ignore[no-untyped-def]
    plan = _user_with_plan(api)
    target = next(m for m in plan["meals"] if m["meal"] and m["slot"] == "breakfast")
    first = target["meal"]["recipe_id"]
    second = api.post(
        f"/meal-plans/current/meals/{target['id']}/replace", {"avoid_recipe_ids": [first]}
    )
    second_id = second.json()["meal"]["meal"]["recipe_id"]
    third = api.post(
        f"/meal-plans/current/meals/{target['id']}/replace",
        {"avoid_recipe_ids": [first, second_id]},
    )
    assert third.status_code == 200
    assert third.json()["meal"]["meal"]["recipe_id"] not in (first, second_id)


def test_generation_and_grocery_meet_response_time_targets(api, seeded) -> None:  # type: ignore[no-untyped-def]
    # SRS §5.1: plan generation ≤ 5 s, grocery list regeneration (after a replacement) ≤ 2 s.
    api.register()
    api.put("/profile", VALID_PROFILE)
    started = perf_counter()
    plan = api.post("/meal-plans/generate").json()
    assert perf_counter() - started <= 5.0

    target = next(m for m in plan["meals"] if m["meal"])
    started = perf_counter()
    assert api.post(f"/meal-plans/current/meals/{target['id']}/replace").status_code == 200
    assert api.get("/grocery-lists/current").status_code == 200
    assert perf_counter() - started <= 2.0

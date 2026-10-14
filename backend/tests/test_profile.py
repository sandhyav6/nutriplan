"""REQ-4.1.3 – REQ-4.1.5 – profile create, validate, edit; nutrition profile in the response."""

from tests.conftest import VALID_PROFILE


def test_profile_missing_returns_404(api) -> None:  # type: ignore[no-untyped-def]
    api.register()
    response = api.get("/profile")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "profile_not_found"


def test_create_profile_returns_nutrition_target(api) -> None:  # type: ignore[no-untyped-def]
    api.register()
    allergens = {a["name"]: a["id"] for a in api.get("/allergens").json()}
    payload = {**VALID_PROFILE, "allergen_ids": [allergens["Peanuts"], allergens["Dairy"]]}
    response = api.put("/profile", payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["nutrition"] == {
        "bmi": "21.5",
        "bmi_category": "normal",
        "baseline_calories_kcal": 2300,
        "daily_calories_kcal": 2300,
        "daily_protein_g": 44,
        "prioritise_weight_loss_meals": False,
    }
    assert {a["name"] for a in body["allergens"]} == {"Peanuts", "Dairy"}
    assert api.get("/auth/me").json()["has_profile"] is True


def test_edit_profile_updates_targets(api) -> None:  # type: ignore[no-untyped-def]
    api.register()
    api.put("/profile", VALID_PROFILE)
    response = api.put(
        "/profile", {**VALID_PROFILE, "health_goal": "muscle_gain", "weekly_budget_inr": "2000"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["weekly_budget_inr"] == "2000.00"
    assert body["nutrition"]["daily_calories_kcal"] == 2600  # Description §8.3
    assert body["nutrition"]["daily_protein_g"] == 120


def test_profile_rejects_invalid_values(api) -> None:  # type: ignore[no-untyped-def]
    api.register()
    cases = [
        {"age": 5},
        {"weight_kg": "-60"},
        {"height_cm": "20"},
        {"weekly_budget_inr": "0"},
        {"max_cooking_time_min": 1},
        {"dietary_preference": "carnivore"},
        {"unexpected": True},
    ]
    for override in cases:
        response = api.put("/profile", {**VALID_PROFILE, **override})
        assert response.status_code == 422, override
        assert response.json()["error"]["code"] == "validation_error"
    missing = {k: v for k, v in VALID_PROFILE.items() if k != "gender"}
    response = api.put("/profile", missing)
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["location"] == ["body", "gender"]


def test_unknown_allergen_rejected(api) -> None:  # type: ignore[no-untyped-def]
    api.register()
    response = api.put("/profile", {**VALID_PROFILE, "allergen_ids": [9999]})
    assert response.status_code == 422


def test_profiles_are_private(make_api) -> None:  # type: ignore[no-untyped-def]
    first, second = make_api(), make_api()
    first.register()
    first.put("/profile", VALID_PROFILE)
    second.register(email="ravi@example.com")
    assert second.get("/profile").status_code == 404

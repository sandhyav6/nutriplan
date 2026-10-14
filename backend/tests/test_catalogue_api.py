"""Admin panel API (REQ-4.7.1 – REQ-4.7.5) and recipe nutrition pre-calculation."""

from decimal import Decimal


def _ids(admin):  # type: ignore[no-untyped-def]
    allergens = {a["name"]: a["id"] for a in admin.get("/allergens").json()}
    categories = {c["slot"]: c["id"] for c in admin.get("/admin/categories").json()}
    return allergens, categories


FOOD = {
    "name": "Test Lentils",
    "food_group": "Pulses & Legumes",
    "diet_type": "vegan",
    "unit": "g",
    "price_inr": "100",
    "price_quantity": "1000",
    "allergen_ids": [],
}
NUTRITION = {
    "per_quantity": "100",
    "calories_kcal": "350",
    "protein_g": "24",
    "carbs_g": "60",
    "fat_g": "1.5",
}


def test_food_nutrition_recipe_crud_and_recalculation(admin_api) -> None:  # type: ignore[no-untyped-def]
    allergens, categories = _ids(admin_api)
    food = admin_api.post("/admin/foods", FOOD)
    assert food.status_code == 201, food.text
    food_id = food.json()["id"]
    assert admin_api.post("/admin/foods", FOOD).status_code == 409  # unique name

    nut = admin_api.put(f"/admin/foods/{food_id}/nutrition", NUTRITION)
    assert nut.status_code == 200
    assert Decimal(nut.json()["nutrition"]["calories_kcal"]) == Decimal("350.00")

    recipe = admin_api.post(
        "/admin/recipes",
        {
            "name": "Test Dal",
            "category_id": categories["lunch"],
            "prep_time_min": 20,
            "ingredients": [{"food_id": food_id, "quantity": "200"}],
        },
    )
    assert recipe.status_code == 201, recipe.text
    body = recipe.json()
    assert Decimal(body["nutrition"]["calories_kcal"]) == Decimal(
        "700.00"
    )  # 200 g at 350 kcal / 100 g
    assert Decimal(body["nutrition"]["estimated_cost_inr"]) == Decimal(
        "20.00"
    )  # 200 g at ₹100 / kg
    assert body["diet_type"] == "vegan"
    assert body["ingredients"][0]["unit"] == "g"

    # Changing a food's price or nutrition recalculates recipes that use it.
    admin_api.put(
        f"/admin/foods/{food_id}", {**FOOD, "price_inr": "150", "allergen_ids": [allergens["Soy"]]}
    )
    updated = admin_api.get(f"/admin/recipes/{body['id']}").json()
    assert Decimal(updated["nutrition"]["estimated_cost_inr"]) == Decimal("30.00")
    assert updated["allergens"] == ["Soy"]

    # A food used by a recipe cannot be deleted or change unit.
    assert admin_api.delete(f"/admin/foods/{food_id}").status_code == 409
    assert admin_api.put(f"/admin/foods/{food_id}", {**FOOD, "unit": "ml"}).status_code == 409

    assert admin_api.delete(f"/admin/recipes/{body['id']}").status_code == 204
    assert admin_api.delete(f"/admin/foods/{food_id}/nutrition").status_code == 204
    assert admin_api.delete(f"/admin/foods/{food_id}").status_code == 204


def test_recipe_validation(admin_api) -> None:  # type: ignore[no-untyped-def]
    _, categories = _ids(admin_api)
    no_ingredients = {
        "name": "Empty",
        "category_id": categories["lunch"],
        "prep_time_min": 10,
        "ingredients": [],
    }
    assert admin_api.post("/admin/recipes", no_ingredients).status_code == 422
    bad_food = {**no_ingredients, "ingredients": [{"food_id": 99999, "quantity": "10"}]}
    assert admin_api.post("/admin/recipes", bad_food).status_code == 422
    bad_category = {**bad_food, "category_id": 999}
    assert admin_api.post("/admin/recipes", bad_category).status_code == 422


def test_categories_are_fixed_but_renamable(admin_api) -> None:  # type: ignore[no-untyped-def]
    categories = admin_api.get("/admin/categories").json()
    assert [c["slot"] for c in categories] == ["breakfast", "lunch", "dinner", "snack"]
    lunch = categories[1]
    renamed = admin_api.put(
        f"/admin/categories/{lunch['id']}", {"name": "Midday Meal", "description": "Main meal"}
    )
    assert renamed.status_code == 200 and renamed.json()["name"] == "Midday Meal"
    created = admin_api.post("/admin/categories", {"name": "Brunch"})
    assert created.status_code == 409 and created.json()["error"]["code"] == "fixed_categories"
    assert admin_api.delete(f"/admin/categories/{lunch['id']}").status_code == 409


def test_seed_dataset_is_complete(seeded, admin_api) -> None:  # type: ignore[no-untyped-def]
    recipes = admin_api.get("/admin/recipes").json()
    assert len(recipes) == 100
    assert all(r["nutrition"] and Decimal(r["nutrition"]["calories_kcal"]) > 0 for r in recipes)
    assert {r["slot"] for r in recipes} == {"breakfast", "lunch", "dinner", "snack"}
    poha = next(r for r in recipes if r["name"] == "Vegetable Poha")
    assert {"Peanuts", "Mustard"} <= set(poha["allergens"])

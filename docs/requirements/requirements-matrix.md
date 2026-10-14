# Requirements Traceability Matrix (SRS v1.0, REQ-4.1.1 – REQ-4.7.5)

Maps every functional requirement to the planned backend module, frontend screen, test
coverage and delivery milestone (see [development-roadmap.md](../development-roadmap.md)).
Paths are relative to the repository root. "M0 status" describes what exists **now**.

Legend – M0 status: **Schema** = tables/constraints exist in the initial migration;
**Shell** = screen layout exists with a development notice; **Stub** = rule-engine interface
exists and raises `NotImplementedError`; **–** = not started.

## 4.1 User Registration and Profile Management (High)

| Req | Summary | Backend (planned) | Frontend | Tests (planned) | Milestone | M0 status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.1.1 | Register with unique email + password | `api/v1/auth.py`, `services/auth_service.py`, `repositories/user_repository.py`, `models/user.py` | `/register` | duplicate email, hashing, role always `user` | M1 | Schema (`uq_users_email`), Shell |
| REQ-4.1.2 | Log in / log out | `api/v1/auth.py`, `core/security.py` | `/login`, header | login success/failure, logout clears session | M1 | Shell |
| REQ-4.1.3 | Capture profile attributes | `api/v1/profiles.py`, `services/profile_service.py`, `schemas/profile.py` | `/profile` | create/read profile | M1 | Schema (`user_profiles`, allergen links), Shell |
| REQ-4.1.4 | Reject missing / out-of-range values with inline errors | Pydantic schemas + DB `CHECK` constraints | `/profile` (React Hook Form + Zod) | validation cases per field | M1 | Schema (range checks) |
| REQ-4.1.5 | Edit any profile attribute | `PUT /api/v1/profile` | `/profile` | update profile | M1 | Shell |

## 4.2 Weekly Meal Recommendation (High)

| Req | Summary | Backend (planned) | Frontend | Tests (planned) | Milestone | M0 status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.2.1 | 7 days × breakfast/lunch/dinner/snack | `rule_engine/planner.py`, `services/meal_plan_service.py`, `api/v1/meal_plans.py` | `/meal-plan` | plan has 28 slots | M3 | Schema (`meal_plans`, `planned_meals` unique day+slot), Stub, Shell |
| REQ-4.2.2 | Exclude meals conflicting with diet | `rule_engine/filters.py::matches_diet` | – | per-diet unit tests | M3 | Stub |
| REQ-4.2.3 | Exclude meals with declared allergens | `rule_engine/filters.py::is_allergen_free`, `validator.py` | `/profile` allergen picker | allergen + excluded-food unit tests, validator test | M3 | Schema (`food_allergens`, `user_profile_allergens`), Stub |
| REQ-4.2.4 | Goal-based filtering | `rule_engine/filters.py::fits_nutrition_target`, `ranking.py` | – | WL / MG / Maintenance cases | M3 | Stub |
| REQ-4.2.5 | Exclude recipes over cooking time | `rule_engine/filters.py::within_cooking_time` | – | boundary (= limit allowed) | M3 | Schema (`recipes.prep_time_min`), Stub |
| REQ-4.2.6 | ≤ 2 repeats per meal per week | `rule_engine/variety.py`, `config.MAX_REPEATS_PER_WEEK` | – | repeat-count property test | M3 | Stub, constant defined |
| REQ-4.2.7 | Approximate weekly nutritional balance | `rule_engine/ranking.py` | `/meal-plan` totals | balance scoring tests | M3 | Stub |
| REQ-4.2.8 | Explain empty slots | `planner.py` → `planned_meals.unavailable_reason` | `/meal-plan` slot message | infeasible-slot test | M3 | Schema (`ck_planned_meals_recipe_or_reason`) |

## 4.3 Grocery List Generator (High)

| Req | Summary | Backend (planned) | Frontend | Tests (planned) | Milestone | M0 status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.3.1 | Aggregate quantities of identical ingredients | `services/grocery_service.py` | `/grocery-list` | 200 g + 300 g = 500 g | M4 | Schema (`grocery_lists`, `grocery_list_items`), Shell |
| REQ-4.3.2 | Remove duplicate entries | `grocery_service.py` | `/grocery-list` | one row per food | M4 | Schema (`uq_grocery_list_items_grocery_list_id_food_id`) |
| REQ-4.3.3 | Regenerate after meal replacement | `meal_plan_service.replace_meal` → `grocery_service` | `/grocery-list` | list changes after replace | M5 | – |
| REQ-4.3.4 | Consistent human-readable units | `grocery_service.py` (g→kg, ml→L) | `/grocery-list` | unit formatting tests | M4 | Schema (canonical units) |

## 4.4 Feedback System (Medium)

| Req | Summary | Backend (planned) | Frontend | Tests (planned) | Milestone | M0 status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.4.1 | Like / Dislike / Skip / Favourite | `api/v1/feedback.py`, `services/feedback_service.py` | `/meal-plan/meals/:id` | submit each type | M5 | Schema, Shell (disabled controls) |
| REQ-4.4.2 | Store user, meal, type, timestamp | `models/feedback.py` | – | persisted fields | M5 | Schema (`feedback`) |
| REQ-4.4.3 | Lower priority after Dislike / Skip | `rule_engine/ranking.py` + `config.FEEDBACK_WEIGHTS` | – | ranking drops | M5 | Stub, weights defined |
| REQ-4.4.4 | Raise priority after Like / Favourite; similar meals for Favourite | `ranking.py`, `variety.similarity` | – | ranking rises, similar boosted | M5 | Stub |

## 4.5 Meal Replacement (High)

| Req | Summary | Backend (planned) | Frontend | Tests (planned) | Milestone | M0 status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.5.1 | Replace any single meal | `POST /api/v1/meal-plans/{id}/meals/{meal_id}/replace` | `/meal-plan/meals/:id` | replace endpoint | M5 | Shell (disabled) |
| REQ-4.5.2 | Same diet and allergy constraints | `planner.find_replacement`, `validator.py` | – | never violates | M5 | Stub |
| REQ-4.5.3 | Weekly budget not exceeded | `planner.find_replacement` | – | budget test | M5 | Stub |
| REQ-4.5.4 | Calories within tolerance | `planner.find_replacement`, `config.REPLACEMENT_CALORIE_TOLERANCE` | – | tolerance boundary | M5 | Stub (tolerance = OD-07) |
| REQ-4.5.5 | Notify when no valid replacement | API 409 with explanation | toast/message | no-candidate case | M5 | – |

## 4.6 Dashboard (Medium)

| Req | Summary | Backend (planned) | Frontend | Tests (planned) | Milestone | M0 status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.6.1 | Total planned weekly calories | `api/v1/dashboard.py`, `services/dashboard_service.py` | `/dashboard` (Recharts) | totals | M6 | Shell |
| REQ-4.6.2 | Estimated spend vs budget | `dashboard_service.py` | `/dashboard` | spend vs budget | M6 | Shell |
| REQ-4.6.3 | Meal statistics | `dashboard_service.py` | `/dashboard` | counts by category/feedback | M6 | Shell |
| REQ-4.6.4 | Favourite meals | `dashboard_service.py` | `/dashboard` | favourites list | M6 | Shell |

## 4.7 Admin Panel (Medium)

| Req | Summary | Backend (planned) | Frontend | Tests (planned) | Milestone | M0 status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.7.1 | Admin role only | `core/security.py::require_admin` dependency | `/admin` route guard | 403 for users | M2 | Schema (`users.role` check) , Shell |
| REQ-4.7.2 | CRUD Foods | `api/v1/admin/foods.py`, `repositories/catalog_repository.py` | `/admin` Foods tab | CRUD tests | M2 | Schema (`foods`, `food_allergens`), Shell |
| REQ-4.7.3 | CRUD Recipes incl. ingredients and prep time | `api/v1/admin/recipes.py` | `/admin` Recipes tab | CRUD + recalculation | M2 | Schema (`recipes`, `recipe_ingredients`, `recipe_nutrition`), Shell |
| REQ-4.7.4 | CRUD Nutrition Values | `api/v1/admin/nutrition.py` | `/admin` Nutrition tab | CRUD tests | M2 | Schema (`food_nutrition`), Shell |
| REQ-4.7.5 | CRUD Categories | `api/v1/admin/categories.py` (see OD-02) | `/admin` Categories tab | update allowed; create/delete rejected | M2 | Schema (4 seeded categories), Shell |

## Non-functional requirements (SRS §5)

| Ref | Requirement | Approach | Milestone |
| --- | --- | --- | --- |
| §5.1 | Plan in ≤ 5 s; grocery regeneration ≤ 2 s | In-memory pure rule engine; timing test | M3 / M4 |
| §5.2 | Allergy safety overrides all rules; "estimates, not medical advice" label | Hard filter + independent validator; footer disclaimer (done in M0) | M0 / M3 |
| §5.3 | Auth for private data, RBAC, salted hashing, HTTPS | M1 security module; HTTPS at deployment | M1 / M6 |
| §5.4 | Usability, determinism, discrete testable rules, availability | Pure rule functions + unit tests; deterministic tie-break | M3 |
| §5.5 | Admin-only catalogue writes; hard > soft rules; one category per recipe | RBAC; filter order; `recipes.category_id NOT NULL` (done in M0) | M0 / M2 / M3 |

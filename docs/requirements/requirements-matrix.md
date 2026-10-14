# Requirements Traceability Matrix (SRS v1.0, REQ-4.1.1 – REQ-4.7.5)

Maps every functional requirement to its backend implementation, frontend screen, automated
tests and delivery milestone (see [development-roadmap.md](../development-roadmap.md)).
Backend paths are relative to `backend/app/`, test files to `backend/tests/` (pytest) and
`frontend/src/` (Vitest). Decisions referenced as OD-xx are in
[open-decisions.md](open-decisions.md).

**Status (Release 1.0, after M6): all 35 functional requirements are implemented and covered
by automated tests.** Status legend: **Done** = implemented and tested.

## 4.1 User Registration and Profile Management (High)

| Req | Summary | Backend | Frontend | Tests | Milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.1.1 | Register with unique email + password | `api/v1/auth.py`, `services/auth_service.py`, `repositories/users.py`, `core/security.py` (Argon2id) | `/register` | `test_auth.py::test_register_creates_user_session_and_never_admin`, `::test_register_duplicate_email_case_insensitive`, `::test_register_rejects_role_field`, `::test_register_validates_password_and_email`; `pages/auth.test.tsx` | M1 | Done |
| REQ-4.1.2 | Log in / log out | `api/v1/auth.py`, `core/security.py`, `core/csrf.py`, `core/deps.py` | `/login`, header | `test_auth.py::test_login_success_and_failure`, `::test_logout_revokes_session`, `::test_session_cookie_is_httponly`, `::test_state_changing_requests_need_csrf_token`; `pages/auth.test.tsx`, `AppLayout.test.tsx` | M1 | Done |
| REQ-4.1.3 | Capture profile attributes | `api/v1/profile.py`, `services/profile_service.py`, `repositories/profiles.py`, `schemas/profile.py`, `rule_engine/nutrition.py` | `/profile` | `test_profile.py::test_create_profile_returns_nutrition_target`; `test_nutrition.py`; `pages/profile.test.tsx` | M1 | Done |
| REQ-4.1.4 | Reject missing / out-of-range values with inline errors | Pydantic schemas + DB `CHECK` constraints | `/profile` (React Hook Form + Zod) | `test_profile.py::test_profile_rejects_invalid_values`, `::test_unknown_allergen_rejected`; `pages/profile.test.tsx` (inline + server field errors) | M1 | Done |
| REQ-4.1.5 | Edit any profile attribute | `PUT /api/v1/profile` | `/profile` | `test_profile.py::test_edit_profile_updates_targets`, `::test_profiles_are_private`; `pages/profile.test.tsx` | M1 | Done |

## 4.2 Weekly Meal Recommendation (High)

| Req | Summary | Backend | Frontend | Tests | Milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.2.1 | 7 days × breakfast/lunch/dinner/snack | `rule_engine/planner.py`, `services/meal_plan_service.py`, `api/v1/plans.py` | `/meal-plan` | `test_rule_engine.py::test_plan_has_seven_days_four_slots_and_is_valid`; `test_plans_api.py::test_generate_plan_respects_constraints`; `pages/plans.test.tsx` | M3 | Done |
| REQ-4.2.2 | Exclude meals conflicting with diet | `rule_engine/filters.py::matches_diet`, `validator.py` | – | `test_rule_engine.py::test_diet_rule_vegetarian_excludes_egg_and_meat`, `::test_hard_constraints_are_never_relaxed`, `::test_validator_catches_violations` | M3 | Done |
| REQ-4.2.3 | Exclude meals with declared allergens | `rule_engine/filters.py::is_allergen_free`, `validator.py` | `/profile` allergen + excluded-food picker | `test_rule_engine.py::test_allergy_rule_uses_allergen_ids_and_excluded_foods`, `::test_validator_catches_violations`; `test_plans_api.py::test_generate_plan_respects_constraints` | M3 | Done |
| REQ-4.2.4 | Goal-based filtering | `rule_engine/nutrition.py` (goal targets, BMI priority), `ranking.py::goal_fit` | `/profile` nutrition summary | `test_nutrition.py::test_calorie_targets`, `::test_weight_loss_floor_and_protein_targets`, `::test_bmi_over_25_raises_weight_loss_priority`; `test_rule_engine.py::test_goal_orientation_changes_ranking` | M3 | Done |
| REQ-4.2.5 | Exclude recipes over cooking time | `rule_engine/filters.py::within_cooking_time` | – | `test_rule_engine.py::test_cooking_time_boundary` (= limit allowed); `test_plans_api.py::test_generate_plan_respects_constraints` | M3 | Done |
| REQ-4.2.6 | ≤ 2 repeats per meal per week | `rule_engine/variety.py`, `config.MAX_REPEATS_PER_WEEK`, `validator.py` | – | `test_rule_engine.py::test_plan_never_repeats_a_meal_more_than_twice`, `::test_too_few_meals_leaves_explained_slots_instead_of_breaking_repeat_limit`, `::test_variety_blocks_repeats_and_near_duplicates` | M3 | Done |
| REQ-4.2.7 | Approximate weekly nutritional balance | `rule_engine/ranking.py` (nutrition fit, balance), `planner.py::choose_servings` (OD-21) | `/meal-plan` daily totals | `test_rule_engine.py::test_plan_meets_calorie_target_approximately`, `::test_weekly_balance_favours_vegetables_and_fruit`, `::test_choose_servings_steps_and_limits` | M3 | Done |
| REQ-4.2.8 | Explain empty slots | `rule_engine/filters.py::explain_empty_slot` → `planned_meals.unavailable_reason`; budget infeasibility (OD-01) | `/meal-plan` slot message | `test_rule_engine.py::test_explain_empty_slot_names_the_constraint`, `::test_empty_slot_when_no_safe_meal_exists`; `test_plans_api.py::test_infeasible_budget_returns_explanation`; `pages/plans.test.tsx` | M3 | Done |

## 4.3 Grocery List Generator (High)

| Req | Summary | Backend | Frontend | Tests | Milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.3.1 | Aggregate quantities of identical ingredients | `services/grocery_service.py` | `/grocery-list` | `test_plans_api.py::test_grocery_list_aggregates_plan_ingredients`; `pages/plans.test.tsx` | M4 | Done |
| REQ-4.3.2 | Remove duplicate entries | `grocery_service.py` (one row per food, `uq_grocery_list_items_grocery_list_id_food_id`) | `/grocery-list` | `test_plans_api.py::test_grocery_list_aggregates_plan_ingredients` | M4 | Done |
| REQ-4.3.3 | Regenerate after meal replacement | `meal_plan_service.replace_meal` → `grocery_service` | `/grocery-list` | `test_plans_api.py::test_replace_meal_updates_plan_and_grocery_list` | M5 | Done |
| REQ-4.3.4 | Consistent human-readable units | `grocery_service.display_quantity` (g→kg, ml→L, pieces) | `/grocery-list` | `test_plans_api.py::test_display_units`; `pages/plans.test.tsx` | M4 | Done |

## 4.4 Feedback System (Medium)

| Req | Summary | Backend | Frontend | Tests | Milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.4.1 | Like / Dislike / Skip / Favourite | `POST /api/v1/feedback`, `services/feedback_service.py` | `/meal-plan/meals/:id` | `test_plans_api.py::test_feedback_and_dashboard`, `::test_feedback_is_private`; `pages/plans.test.tsx` | M5 | Done |
| REQ-4.4.2 | Store user, meal, type, timestamp | `models/feedback.py` | – | `test_plans_api.py::test_feedback_and_dashboard` (stored row assertions) | M5 | Done |
| REQ-4.4.3 | Lower priority after Dislike / Skip | `rule_engine/ranking.py` + `config.FEEDBACK_WEIGHTS` | – | `test_rule_engine.py::test_feedback_changes_ranking` | M5 | Done |
| REQ-4.4.4 | Raise priority after Like / Favourite; similar meals for Favourite | `ranking.py`, `variety.favourite_affinity` | – | `test_rule_engine.py::test_feedback_changes_ranking`, `::test_favourite_boosts_similar_meals` | M5 | Done |

## 4.5 Meal Replacement (High)

| Req | Summary | Backend | Frontend | Tests | Milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.5.1 | Replace any single meal | `POST /api/v1/meal-plans/current/meals/{id}/replace` | `/meal-plan/meals/:id` | `test_plans_api.py::test_replace_meal_updates_plan_and_grocery_list`, `::test_repeated_replacement_does_not_bounce_back`; `pages/plans.test.tsx` | M5 | Done |
| REQ-4.5.2 | Same diet and allergy constraints | `planner.find_replacement`, `validator.py` | – | `test_rule_engine.py::test_replacement_keeps_constraints_and_calorie_tolerance` | M5 | Done |
| REQ-4.5.3 | Weekly budget not exceeded | `planner.find_replacement` | – | `test_rule_engine.py::test_replacement_keeps_constraints_and_calorie_tolerance`, `::test_validator_catches_budget_and_repeats` | M5 | Done |
| REQ-4.5.4 | Calories within tolerance (±20 %, OD-07) | `planner.find_replacement`, `config.REPLACEMENT_CALORIE_TOLERANCE` | – | `test_rule_engine.py::test_replacement_keeps_constraints_and_calorie_tolerance` | M5 | Done |
| REQ-4.5.5 | Notify when no valid replacement | API 409 `no_replacement` with explanation | meal-details message | `test_rule_engine.py::test_replacement_reports_when_none_exists`; `pages/plans.test.tsx` | M5 | Done |

## 4.6 Dashboard (Medium)

| Req | Summary | Backend | Frontend | Tests | Milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.6.1 | Total planned weekly calories | `GET /api/v1/dashboard`, `services/dashboard_service.py` | `/dashboard` (Recharts daily chart) | `test_plans_api.py::test_feedback_and_dashboard`, `::test_dashboard_without_plan`; `pages/plans.test.tsx` | M6 | Done |
| REQ-4.6.2 | Estimated spend vs budget | `dashboard_service.py` | `/dashboard` | `test_plans_api.py::test_feedback_and_dashboard`; `pages/plans.test.tsx` | M6 | Done |
| REQ-4.6.3 | Meal statistics | `dashboard_service.py` (meals by slot, feedback counts, empty slots) | `/dashboard` | `test_plans_api.py::test_feedback_and_dashboard`; `pages/plans.test.tsx` | M6 | Done |
| REQ-4.6.4 | Favourite meals | `dashboard_service.py` | `/dashboard` | `test_plans_api.py::test_feedback_and_dashboard`; `pages/plans.test.tsx` | M6 | Done |

## 4.7 Admin Panel (Medium)

| Req | Summary | Backend | Frontend | Tests | Milestone | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-4.7.1 | Admin role only | `core/deps.py::require_admin`, `cli.py create-admin` | `/admin` route guard (`app/guards.tsx`) | `test_auth.py::test_admin_routes_enforce_role`, `::test_cli_create_admin_reads_environment`; `app/routes.test.tsx` | M2 | Done |
| REQ-4.7.2 | CRUD Foods | `api/v1/admin.py`, `services/catalogue_service.py` | `/admin` Foods tab (`features/admin/FoodsPanel.tsx`) | `test_catalogue_api.py::test_food_nutrition_recipe_crud_and_recalculation` | M2 | Done |
| REQ-4.7.3 | CRUD Recipes incl. ingredients and prep time | `api/v1/admin.py`, `catalogue_service.py` (nutrition & cost recalculation, OD-16) | `/admin` Recipes tab | `test_catalogue_api.py::test_food_nutrition_recipe_crud_and_recalculation`, `::test_recipe_validation`, `::test_seed_dataset_is_complete` | M2 | Done |
| REQ-4.7.4 | CRUD Nutrition Values | `PUT/DELETE /api/v1/admin/foods/{id}/nutrition` | `/admin` Nutrition tab | `test_catalogue_api.py::test_food_nutrition_recipe_crud_and_recalculation` | M2 | Done |
| REQ-4.7.5 | CRUD Categories (OD-02) | `api/v1/admin.py` – read/update; create/delete → 409 | `/admin` Categories tab | `test_catalogue_api.py::test_categories_are_fixed_but_renamable` | M2 | Done |

## Non-functional requirements (SRS §5)

| Ref | Requirement | Implementation | Tests | Status |
| --- | --- | --- | --- | --- |
| §5.1 | Plan in ≤ 5 s; grocery regeneration ≤ 2 s | In-memory pure rule engine | `test_plans_api.py::test_generation_and_grocery_meet_response_time_targets` | Done |
| §5.2 | Allergy safety overrides all rules; "estimates, not medical advice" label | Hard filter + independent validator before storing; footer, profile and meal disclaimers | `test_rule_engine.py::test_hard_constraints_are_never_relaxed`; `AppLayout.test.tsx` | Done |
| §5.3 | Auth for private data, RBAC, salted hashing, HTTPS | Argon2id, HttpOnly session cookie, CSRF, `require_user` / `require_admin`, per-user queries; Secure cookies in production, HTTPS at the reverse proxy | `test_auth.py`, `test_profile.py::test_profiles_are_private`, `test_plans_api.py::test_feedback_is_private` | Done (HTTPS: deployment) |
| §5.4 | Usability, determinism, discrete testable rules, availability | Pure rule functions; tie-break by id; keyboard-accessible UI with landmarks and skip link; health endpoint + container health check | `test_rule_engine.py::test_plan_is_deterministic`, `test_health.py`, `AppLayout.test.tsx` | Done |
| §5.5 | Admin-only catalogue writes; hard > soft rules; one category per recipe | RBAC; filter order; `recipes.category_id NOT NULL` | `test_auth.py::test_admin_routes_enforce_role`, `test_models.py::test_recipe_requires_exactly_one_category` | Done |

## PostgreSQL integration tests

`test_db_integration.py` (marked `integration`, run when `TEST_DATABASE_URL` is set and in CI):
migration upgrade/downgrade round-trip, database-level enum check, and the full user flow
(seed → register → profile → plan → feedback → replace → grocery list → dashboard) on
PostgreSQL. All other tests use in-memory SQLite.

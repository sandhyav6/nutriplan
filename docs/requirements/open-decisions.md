# Open Decisions and Assumptions

This file records ambiguities in the requirements and the implementation choices made
(or still pending) to resolve them. **SRS v1.0** (`NutriPlan-SRS.docx`) is the Release 1.0
baseline; the **Detailed Project Description** (`NutriPlan-Project-Description.docx`) is the
supporting architecture/business-logic reference. Nothing here overrides either document –
each entry separates *what the documents say* from *what we assume*.

Status values: **Decided** (implemented or fixed for the next milestone), **Proposed**
(recommended – confirm with the Product Owner), **Open** (needs a decision before the
milestone shown).

| ID | Topic | Status | Needed by |
| --- | --- | --- | --- |
| OD-01 | Meaning of "closest feasible plan" | Proposed | M3 |
| OD-02 | Admin CRUD on categories vs four fixed categories | Decided | M2 |
| OD-03 | Which constraints are hard | Decided | M3 |
| OD-04 | Rule numbering differs between documents | Decided | – |
| OD-05 | Calorie/budget share per meal slot | Open | M3 |
| OD-06 | Calorie adjustment for Weight Loss / Muscle Gain | Open | M1 |
| OD-07 | Replacement calorie tolerance | Open | M5 |
| OD-08 | Definition of "category similarity" for variety | Open | M3 |
| OD-09 | Dietary preference values | Decided | M1 |
| OD-10 | Representation of allergies | Decided | M1 |
| OD-11 | Use of age and gender in targets | Proposed | M1 |
| OD-12 | Session / token mechanism and CSRF | Proposed | M1 |
| OD-13 | Python version | Decided | – |
| OD-14 | When to install React Hook Form, Zod, Recharts | Decided | M1 / M6 |
| OD-15 | Source and labelling of the food dataset | Proposed | M2 |
| OD-16 | Recipe nutrition: derived or entered | Proposed | M2 |
| OD-17 | REQ-4.2.6 when fewer than four valid meals exist | Proposed | M3 |
| OD-18 | Week start day | Proposed | M3 |
| OD-19 | User documentation format (SRS TBD-2) | Open | M6 |
| OD-20 | Hosting, uptime and concurrency targets (SRS TBD-1/3/4) | Open | M6 |

---

### OD-01 – "Closest feasible plan"
**Documents:** SRS §4.2.2: "Rule engine cannot satisfy all constraints simultaneously (e.g.,
budget cannot be met) → System displays a warning and the closest feasible plan." SRS §2.5
and §5.5: diet, allergies and budget are hard constraints that "may never be overridden".

**Tension:** a plan that exceeds the budget is not "feasible" under §2.5.

**Proposed interpretation:** "closest feasible" never means violating a hard constraint.
* Every meal shown always satisfies diet, allergy and cooking-time rules.
* If the weekly budget cannot be met, the engine reports *infeasible* with an explanation
  (which constraint conflicts, the lowest achievable weekly cost) and does **not** save an
  over-budget plan as the user's active plan. The user can then adjust budget or other inputs.
* Slots for which no safe meal exists carry an explanation (REQ-4.2.8) instead of a recipe.
* Soft goals (nutrition fit, variety, balance) may be approximated, with a warning.

### OD-02 – Category CRUD vs fixed categories
**Documents:** REQ-4.7.5 asks for create/read/update/delete of meal categories; SRS §2.5,
§5.5 and Appendix A define exactly four categories (breakfast, lunch, dinner, snack), and
every recipe belongs to exactly one.

**Decision:** the four categories are seeded by the initial migration and identified by a
fixed `slot` enum. Administrators can **read and update** a category's display name and
description. **Create/delete** are exposed but rejected with a clear validation message,
because adding or removing a category would break the 7×4 plan structure. This satisfies the
CRUD screens while preserving the documented domain rule.

### OD-03 – Hard constraints
**Documents:** SRS §2.5 lists diet type, allergies and budget. REQ-4.2.5 says recipes over
the cooking-time limit "shall" be excluded. §5.2: allergy safety overrides everything.

**Decision:** hard (never relaxed) = dietary preference, declared allergens/excluded foods,
cooking-time limit, weekly budget. Soft (ranked/approximated) = nutrition fit, variety
similarity, weekly food-group balance, feedback preference.

### OD-04 – Rule numbering
SRS Appendix B.3 and Project Description §10.1 number the rules differently (e.g. allergy is
Rule 6 in the SRS and Rule 5 in the Description; BMI priority is Rule 6 in the Description).
Code comments cite **both** sources by name and requirement ID rather than by number alone.

### OD-05 – Per-slot shares
The Description derives a per-meal budget from the daily budget (§10.2) but gives no split.
**Open:** proposed default breakfast 25 %, lunch 35 %, dinner 30 %, snack 10 % for both
calories and budget. Configured in `backend/app/rule_engine/config.py` (`SLOT_SHARES`).

### OD-06 – Goal calorie adjustment
**Documents:** baselines 1800/2300/2800 kcal by activity (§8.1); Muscle Gain → protein
≥ 120 g, calories ≈ 2600 (§8.3); Weight Loss → "calories below target, protein above
minimum" (no numbers). **Open:** proposed Weight Loss = baseline − 500 kcal (floor 1200);
Muscle Gain = baseline + 300 kcal (= 2600 for a moderately active user, matching §8.3);
protein minimums per goal to be agreed. Stored in `config.GOAL_CALORIE_ADJUSTMENT_KCAL`.

### OD-07 – Replacement tolerance
REQ-4.5.4 requires the replacement to be "within an acceptable tolerance" of the original
calories. **Open:** proposed ±20 %.

### OD-08 – Variety similarity
Description stage 8 compares candidates with recent meals "by category similarity" against a
threshold; the SRS (REQ-4.2.6) only limits repeats to two per week. **Open:** proposed
similarity = weighted overlap of main ingredients + macro profile; threshold 0.8.

### OD-09 – Dietary preferences
Documents give "vegetarian, vegan, etc.". **Decided:** `vegan`, `vegetarian`, `eggetarian`,
`non_vegetarian` (eggetarian is common in India and matches the Description's example that a
vegetarian profile removes *egg omelette*). A recipe's diet type is derived from its foods.

### OD-10 – Allergies
REQ-4.2.3 excludes meals "containing an ingredient matching a user-declared allergy".
**Decided:** allergies are structural – a reference `allergens` table linked to foods
(`food_allergens`) and profiles (`user_profile_allergens`), plus `user_profile_excluded_foods`
for ingredient-specific reactions (e.g. mushrooms). Filtering joins on ids, not free text.

### OD-11 – Age and gender
REQ-4.1.3 captures age and gender, but the Description's calorie baselines depend only on
activity level. **Proposed:** store both (required), use them for validation and display in
Phase 1, and do not change the documented baselines. A formula such as Mifflin-St Jeor would be
a requirements change.

### OD-12 – Authentication mechanism
SRS §5.3 requires authentication, RBAC and salted hashing; the mechanism is not specified.
**Proposed for M1:** Argon2id or bcrypt hashing; short-lived session token in an `HttpOnly`,
`Secure`, `SameSite=Lax` cookie; CSRF protection on state-changing requests (double-submit
token header); registration always creates role `user`; admins are promoted by a CLI/seed
command reading credentials from environment variables.

### OD-13 – Python version
The master plan specifies Python 3.13. The development machine has Python 3.14 only, and the
Product Owner chose to **use 3.14** (`requires-python >= 3.14`, CI on 3.14). All pinned
packages were installed and tested on 3.14.

### OD-14 – Library timing
React Hook Form + Zod (forms) and Recharts (dashboard) are part of the stack but are
installed in the milestone that first uses them (M1 and M6) so the scaffold has no unused
dependencies. TypeScript is pinned to 6.0.x because `typescript-eslint` does not yet support 7.x.

### OD-15 – Food dataset
SRS §2.7 assumes an accurate food database; no source is specified. **Proposed:** a small
development dataset clearly labelled *illustrative* (approximate public reference values and
indicative ₹ prices), replaceable through the admin panel. It must never be presented as
verified nutrition or price data.

### OD-16 – Recipe nutrition
SRS §2.7: recipe nutrition values are pre-calculated. **Proposed:** compute
`recipe_nutrition` (and estimated cost) from ingredients whenever a recipe or one of its
foods changes, with no manual override in Release 1.0.

### OD-17 – Fewer than four safe meals for a slot
With at most two repeats (REQ-4.2.6), seven days need ≥ 4 distinct meals per slot.
**Proposed:** never exceed two repeats; remaining slots carry an explanation (REQ-4.2.8)
suggesting which input to relax.

### OD-18 – Week start
**Proposed:** plans start on Monday of the current week (`planned_meals.day_of_week` 0 =
Monday).

### OD-19 / OD-20 – SRS TBD items
User documentation format (TBD-2), hosting provider/OS/DB engine (TBD-1 – PostgreSQL is now
chosen), concurrency (TBD-3) and uptime SLA (TBD-4) remain open until M6.

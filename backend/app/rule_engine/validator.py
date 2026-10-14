"""Stage 10 – independent constraint validator.

Re-checks a finished plan (or a plan after one replacement) against the non-negotiable
constraints: diet, allergens/excluded foods, cooking time, weekly budget and the two-repeat
limit. Kept separate from candidate generation so the future Phase 2 personalisation layer
can be validated by exactly the same code before anything reaches the user.
"""

from collections import Counter
from decimal import Decimal

from app.rule_engine import config
from app.rule_engine.filters import is_allergen_free, matches_diet, within_cooking_time
from app.rule_engine.types import PlannedSlot, PlanResult, ProfileInput, ValidationResult


def validate_slots(
    slots: tuple[PlannedSlot, ...] | list[PlannedSlot], profile: ProfileInput
) -> ValidationResult:
    violations: list[str] = []
    total = Decimal("0")
    counts: Counter[int] = Counter()
    for s in slots:
        if s.portion is None:
            if not s.unavailable_reason:
                violations.append(
                    f"Day {s.day_of_week} {s.slot.value}: empty slot without explanation"
                )
            continue
        c = s.portion.candidate
        where = f"Day {s.day_of_week} {s.slot.value} ({c.name})"
        if c.slot != s.slot:
            violations.append(f"{where}: wrong meal category")
        if not matches_diet(c, profile):
            violations.append(f"{where}: violates dietary preference")
        if not is_allergen_free(c, profile):
            violations.append(f"{where}: contains a declared allergen or excluded food")
        if not within_cooking_time(c, profile):
            violations.append(f"{where}: exceeds cooking-time limit")
        total += s.portion.cost_inr
        counts[c.recipe_id] += 1
    for recipe_id, n in counts.items():
        if n > config.MAX_REPEATS_PER_WEEK:
            violations.append(
                f"Recipe {recipe_id} appears {n} times (limit {config.MAX_REPEATS_PER_WEEK})"
            )
    if total > profile.weekly_budget_inr:
        violations.append(f"Weekly cost ₹{total} exceeds budget ₹{profile.weekly_budget_inr}")
    return ValidationResult(is_valid=not violations, violations=tuple(violations))


def validate_plan(plan: PlanResult, profile: ProfileInput) -> ValidationResult:
    return validate_slots(plan.slots, profile)

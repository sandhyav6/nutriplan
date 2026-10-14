"""Stage 9 – weekly planner and single-meal replacement.

Pipeline per slot: hard filters → portion sizing (OD-21) → ranking → first-choice pool
(nutrition target + per-meal budget) → variety check → assignment. Afterwards Rule 3 enforces
the weekly budget by replacing the highest-cost meals first. If the budget still cannot be
met, an ``Infeasibility`` is returned instead of an over-budget plan (OD-01).
Everything is deterministic: identical inputs give identical plans.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from app.models.enums import MealSlot
from app.rule_engine import config
from app.rule_engine.filters import (
    eligible_candidates,
    explain_empty_slot,
    fits_nutrition_target,
    within_meal_budget,
)
from app.rule_engine.nutrition import calculate_budget_breakdown, slot_targets
from app.rule_engine.ranking import RankingContext, rank_portions
from app.rule_engine.types import (
    BudgetBreakdown,
    Infeasibility,
    MealCandidate,
    NutritionTarget,
    PlannedSlot,
    PlanNote,
    PlanResult,
    Portion,
    ProfileInput,
)
from app.rule_engine.variety import passes_variety

STEP = Decimal(config.SERVING_STEP)
MIN_SERVINGS = Decimal(config.MIN_SERVINGS)
MAX_SERVINGS = Decimal(config.MAX_SERVINGS)


@dataclass(frozen=True)
class PlannerInput:
    profile: ProfileInput
    target: NutritionTarget
    candidates: Sequence[MealCandidate]
    feedback_scores: Mapping[int, int] = field(default_factory=dict)
    favourite_ids: frozenset[int] = frozenset()
    recent_recipe_ids: frozenset[int] = frozenset()


def choose_servings(candidate: MealCandidate, target_calories: float) -> Decimal:
    """Nearest quarter-portion that meets the calorie target, within 0.75–2 servings."""
    if candidate.calories_kcal <= 0 or target_calories <= 0:
        return Decimal("1.00")
    ideal = Decimal(str(target_calories / candidate.calories_kcal))
    stepped = (ideal / STEP).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * STEP
    return min(MAX_SERVINGS, max(MIN_SERVINGS, stepped)).quantize(Decimal("0.01"))


def _sugar_limit(target: NutritionTarget, share: float) -> float:
    # ≤ 10 % of energy from sugars (4 kcal/g), split by slot share.
    return target.daily_calories_kcal * 0.10 / 4 * share


def _context(
    inp: PlannerInput,
    budget: BudgetBreakdown,
    slot: MealSlot,
    calorie_target: float,
    protein_target: float,
    **extra: object,
) -> RankingContext:
    return RankingContext(
        goal=inp.profile.health_goal,
        calorie_target=calorie_target,
        protein_target=protein_target,
        sugar_limit=_sugar_limit(inp.target, config.SLOT_SHARES[slot]),
        per_meal_budget_inr=budget.per_meal_inr[slot],
        prioritise_weight_loss_meals=inp.target.prioritise_weight_loss_meals,
        feedback_scores=inp.feedback_scores,
        favourites=[c for c in inp.candidates if c.recipe_id in inp.favourite_ids],
        recent_recipe_ids=inp.recent_recipe_ids,
        **extra,  # type: ignore[arg-type]
    )


def _counts(slots: Sequence[PlannedSlot], skip: int = -1) -> Counter[int]:
    return Counter(
        s.portion.candidate.recipe_id for i, s in enumerate(slots) if s.portion and i != skip
    )


def _day_ids(slots: Sequence[PlannedSlot], day: int, skip: int = -1) -> set[int]:
    return {
        s.portion.candidate.recipe_id
        for i, s in enumerate(slots)
        if s.portion and s.day_of_week == day and i != skip
    }


def _total_cost(slots: Sequence[PlannedSlot]) -> Decimal:
    return sum((s.portion.cost_inr for s in slots if s.portion), Decimal("0"))


def minimum_weekly_cost(pools: Mapping[MealSlot, list[MealCandidate]]) -> Decimal:
    """Lowest achievable weekly cost under the hard constraints and the two-repeat limit."""
    total = Decimal("0")
    for pool in pools.values():
        costs = sorted(Portion(c, MIN_SERVINGS).cost_inr for c in pool)
        picks = [cost for cost in costs for _ in range(config.MAX_REPEATS_PER_WEEK)]
        total += sum(picks[: config.DAYS_PER_PLAN], Decimal("0"))
    return total


def generate_weekly_plan(inp: PlannerInput) -> PlanResult | Infeasibility:
    """Assemble 7 days x 4 slots (REQ-4.2.1) without ever breaking a hard constraint."""
    profile, target = inp.profile, inp.target
    budget = calculate_budget_breakdown(profile.weekly_budget_inr)
    targets = slot_targets(target)
    pools = {slot: eligible_candidates(inp.candidates, profile, slot) for slot in config.MEAL_SLOTS}

    slots: list[PlannedSlot] = []
    counts: Counter[int] = Counter()
    vegetable_meals = fruit_meals = 0
    short_slots: set[MealSlot] = set()

    for day in range(config.DAYS_PER_PLAN):
        day_ids: set[int] = set()
        day_calories = day_protein = 0.0
        for position, slot in enumerate(config.MEAL_SLOTS):
            pool = pools[slot]
            if not pool:
                slots.append(
                    PlannedSlot(day, slot, None, explain_empty_slot(slot, inp.candidates, profile))
                )
                continue

            # Spread what is left of today's targets over the remaining meals.
            share = config.SLOT_SHARES[slot]
            remaining = sum(config.SLOT_SHARES[s] for s in config.MEAL_SLOTS[position:])
            static_cal, static_pro = targets[slot]
            cal = min(
                static_cal * 1.4,
                max(
                    static_cal * 0.6,
                    (target.daily_calories_kcal - day_calories) * share / remaining,
                ),
            )
            pro = min(
                static_pro * 1.6,
                max(static_pro * 0.6, (target.daily_protein_g - day_protein) * share / remaining),
            )

            ranked = rank_portions(
                (Portion(c, choose_servings(c, cal)) for c in pool),
                _context(
                    inp,
                    budget,
                    slot,
                    cal,
                    pro,
                    weekly_counts=counts,
                    need_vegetable=vegetable_meals < config.VEGETABLE_MEALS_PER_DAY * (day + 1),
                    need_fruit=fruit_meals < config.FRUIT_MEALS_PER_DAY * (day + 1),
                ),
            )
            first_choice = [
                r
                for r in ranked
                if fits_nutrition_target(r.portion, cal, pro, profile.health_goal)
                and within_meal_budget(r.portion, budget.per_meal_inr[slot])
            ]
            order = first_choice + [r for r in ranked if r not in first_choice]
            previous = next(
                (
                    s.portion.candidate
                    for s in slots
                    if s.day_of_week == day - 1 and s.slot == slot and s.portion
                ),
                None,
            )
            chosen = next(
                (
                    r.portion
                    for r in order
                    if passes_variety(r.portion.candidate, counts, day_ids, previous)
                ),
                None,
            ) or next(
                (
                    r.portion
                    for r in order
                    if passes_variety(r.portion.candidate, counts, day_ids, strict=False)
                ),
                None,
            )
            if chosen is None:
                short_slots.add(slot)
                slots.append(
                    PlannedSlot(
                        day,
                        slot,
                        None,
                        f"Only {len(pool)} different {slot.value} meal(s) fit your diet, allergies "
                        "and cooking time, and a meal may appear at most twice a week. Allow more "
                        "cooking time or fewer restrictions to fill this slot.",
                    )
                )
                continue

            c = chosen.candidate
            counts[c.recipe_id] += 1
            day_ids.add(c.recipe_id)
            day_calories += chosen.calories_kcal
            day_protein += chosen.protein_g
            vegetable_meals += c.has_vegetable
            fruit_meals += c.has_fruit
            slots.append(PlannedSlot(day, slot, chosen))

    if not _enforce_weekly_budget(slots, pools, inp, budget, targets):
        minimum = minimum_weekly_cost(pools)
        return Infeasibility(
            code="budget_infeasible",
            message=(
                f"A safe plan cannot fit your weekly budget of ₹{profile.weekly_budget_inr:,.0f}. "
                f"The lowest-cost plan that respects your diet, allergies and cooking time costs "
                f"about ₹{minimum:,.0f}. Increase your budget or allow more cooking time."
            ),
            minimum_weekly_cost_inr=minimum,
        )

    return PlanResult(slots=tuple(slots), notes=_notes(slots, pools, inp, short_slots))


def _enforce_weekly_budget(
    slots: list[PlannedSlot],
    pools: Mapping[MealSlot, list[MealCandidate]],
    inp: PlannerInput,
    budget: BudgetBreakdown,
    targets: Mapping[MealSlot, tuple[float, float]],
) -> bool:
    """Rule 3 – replace the highest-cost meals first; then trim portions. True if within budget."""
    for _ in range(400):
        if _total_cost(slots) <= budget.weekly_inr:
            return True
        order = sorted(
            (i for i, s in enumerate(slots) if s.portion),
            key=lambda i: (-slots[i].portion.cost_inr, i),  # type: ignore[union-attr]
        )
        if _replace_with_cheaper(slots, order, pools, inp, budget, targets):
            continue
        # No cheaper recipe anywhere: reduce the most expensive portion by one step.
        for i in order:
            current = slots[i].portion
            assert current is not None
            if current.servings - STEP >= MIN_SERVINGS:
                slots[i] = PlannedSlot(
                    slots[i].day_of_week,
                    slots[i].slot,
                    Portion(current.candidate, current.servings - STEP),
                )
                break
        else:
            return False
    return _total_cost(slots) <= budget.weekly_inr


def _replace_with_cheaper(slots, order, pools, inp, budget, targets) -> bool:  # type: ignore[no-untyped-def]
    for i in order:
        current = slots[i].portion
        slot = slots[i].slot
        counts = _counts(slots, skip=i)
        today = _day_ids(slots, slots[i].day_of_week, skip=i)
        cal, pro = targets[slot]
        cheaper = [
            p
            for c in pools[slot]
            if c.recipe_id != current.candidate.recipe_id
            and passes_variety(c, counts, today, strict=False)
            and (p := Portion(c, choose_servings(c, cal))).cost_inr < current.cost_inr
        ]
        if cheaper:
            best = rank_portions(cheaper, _context(inp, budget, slot, cal, pro))[0].portion
            slots[i] = PlannedSlot(slots[i].day_of_week, slot, best)
            return True
    return False


def _notes(slots, pools, inp, short_slots) -> tuple[PlanNote, ...]:  # type: ignore[no-untyped-def]
    notes: list[PlanNote] = []
    for slot in config.MEAL_SLOTS:
        if not pools[slot]:
            notes.append(
                PlanNote(
                    "unavailable",
                    f"{slot.value.capitalize()}: "
                    + explain_empty_slot(slot, inp.candidates, inp.profile),
                )
            )
        elif slot in short_slots:
            notes.append(
                PlanNote(
                    "variety",
                    f"Some {slot.value} slots are empty because too few {slot.value} meals "
                    "fit your constraints and no meal may repeat more than twice a week "
                    "(REQ-4.2.6).",
                )
            )
    filled = [s.portion for s in slots if s.portion]
    if filled:
        avg_cal = sum(p.calories_kcal for p in filled) / config.DAYS_PER_PLAN
        avg_pro = sum(p.protein_g for p in filled) / config.DAYS_PER_PLAN
        target = inp.target
        if abs(avg_cal - target.daily_calories_kcal) > target.daily_calories_kcal * 0.15:
            notes.append(
                PlanNote(
                    "nutrition",
                    f"This plan averages {avg_cal:.0f} kcal/day against your target of "
                    f"{target.daily_calories_kcal} kcal/day – the closest the catalogue allows "
                    "within your constraints.",
                )
            )
        if avg_pro < target.daily_protein_g * 0.8:
            notes.append(
                PlanNote(
                    "nutrition",
                    f"Protein averages {avg_pro:.0f} g/day against your {target.daily_protein_g} g "
                    "target. Marking high-protein meals as favourites helps the planner "
                    "prioritise them.",
                )
            )
    return tuple(notes)


@dataclass(frozen=True)
class ReplacementResult:
    portion: Portion | None
    reason: str | None = None


def find_replacement(
    inp: PlannerInput,
    slots: Sequence[PlannedSlot],
    index: int,
    avoid_recipe_ids: frozenset[int] = frozenset(),
) -> ReplacementResult:
    """UC-10 / REQ-4.5.x – an alternative with the same diet & allergy constraints, calories
    within ±20 % of the original, no weekly-budget overrun and no repeat-limit breach.
    ``avoid_recipe_ids`` (meals already swapped out of this slot) are skipped while other
    valid options exist, so repeated replacements do not bounce between two meals."""
    profile = inp.profile
    item = slots[index]
    slot = item.slot
    budget = calculate_budget_breakdown(profile.weekly_budget_inr)
    static_cal, static_pro = slot_targets(inp.target)[slot]
    original = item.portion
    reference = original.calories_kcal if original else static_cal
    tolerance = config.REPLACEMENT_CALORIE_TOLERANCE
    others_cost = _total_cost([s for i, s in enumerate(slots) if i != index])
    counts = _counts(slots, skip=index)
    today = _day_ids(slots, item.day_of_week, skip=index)

    options: list[Portion] = []
    for c in eligible_candidates(inp.candidates, profile, slot):  # REQ-4.5.2
        if original and c.recipe_id == original.candidate.recipe_id:
            continue
        if not passes_variety(c, counts, today, strict=False):
            continue
        portion = Portion(c, choose_servings(c, reference))
        if abs(portion.calories_kcal - reference) > reference * tolerance:  # REQ-4.5.4
            continue
        if others_cost + portion.cost_inr > profile.weekly_budget_inr:  # REQ-4.5.3
            continue
        options.append(portion)

    if not options:  # REQ-4.5.5
        low, high = reference * (1 - tolerance), reference * (1 + tolerance)
        return ReplacementResult(
            None,
            f"No other {slot.value} meal fits your diet, allergies, cooking time, weekly budget "
            f"and calorie range ({low:.0f}–{high:.0f} kcal). Your current meal has been kept.",
        )
    fresh = [p for p in options if p.candidate.recipe_id not in avoid_recipe_ids]
    options = fresh or options
    protein = max(original.protein_g if original else 0.0, static_pro)
    best = rank_portions(options, _context(inp, budget, slot, reference, protein))[0]
    return ReplacementResult(best.portion)

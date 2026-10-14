"""Stage 7 – ranking of candidates that already satisfy every hard constraint.

The score combines nutrition fit, budget fit and the user's weighted feedback
(``config.FEEDBACK_WEIGHTS``), plus Rule 6 (BMI > 25 favours weight-loss meals), Rule 8
(favourites promote similar meals), weekly variety and food-group balance (REQ-4.2.7).
Weights live in ``config.RANKING_WEIGHTS``. Ties are broken by recipe id → deterministic.
"""

from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal

from app.models.enums import HealthGoal
from app.rule_engine import config
from app.rule_engine.types import MealCandidate, Portion, RankedCandidate
from app.rule_engine.variety import favourite_affinity


@dataclass(frozen=True)
class RankingContext:
    goal: HealthGoal
    calorie_target: float
    protein_target: float
    sugar_limit: float
    per_meal_budget_inr: Decimal
    prioritise_weight_loss_meals: bool = False
    feedback_scores: Mapping[int, int] = field(default_factory=dict)
    favourites: Collection[MealCandidate] = ()
    recent_recipe_ids: Collection[int] = frozenset()
    weekly_counts: Mapping[int, int] = field(default_factory=dict)
    need_vegetable: bool = False
    need_fruit: bool = False


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _protein_density(p: Portion) -> float:
    return (p.protein_g * 4) / p.calories_kcal if p.calories_kcal else 0.0


def goal_fit(p: Portion, ctx: RankingContext) -> float:
    """REQ-4.2.4 – 0..1, how well the meal suits the health goal."""
    if ctx.goal is HealthGoal.WEIGHT_LOSS:  # low-calorie, high-protein, low-sugar
        protein = min(1.0, _protein_density(p) / 0.3)
        low_sugar = 1 - min(1.0, p.sugar_g / max(1.0, ctx.sugar_limit))
        below = 1.0 if p.calories_kcal <= ctx.calorie_target else 0.0
        return 0.5 * protein + 0.3 * low_sugar + 0.2 * below
    if ctx.goal is HealthGoal.MUSCLE_GAIN:  # high-protein, higher-calorie, complex carbs
        protein = min(1.0, p.protein_g / max(1.0, ctx.protein_target))
        complex_carbs = min(1.0, p.fibre_g / 8)
        energy = 1.0 if p.calories_kcal >= ctx.calorie_target * 0.9 else 0.0
        return 0.5 * protein + 0.25 * complex_carbs + 0.25 * energy
    total = p.protein_g * 4 + p.carbs_g * 4 + p.fat_g * 9  # balanced ≈ 20/50/30
    if not total:
        return 0.0
    distance = (
        abs(p.protein_g * 4 / total - 0.2)
        + abs(p.carbs_g * 4 / total - 0.5)
        + abs(p.fat_g * 9 / total - 0.3)
    )
    return 1 - min(1.0, distance)


def score_portion(p: Portion, ctx: RankingContext) -> float:
    w = config.RANKING_WEIGHTS
    c = p.candidate
    nutrition_fit = 1 - min(
        1.0, abs(p.calories_kcal - ctx.calorie_target) / max(1.0, ctx.calorie_target)
    )
    protein_fit = min(1.0, p.protein_g / max(1.0, ctx.protein_target))
    budget = float(ctx.per_meal_budget_inr)
    cost = float(p.cost_inr)
    budget_fit = _clamp(1 - cost / budget, 0, 1) if budget > 0 else 0.0
    over_budget = 1.0 if cost > budget else 0.0
    feedback = _clamp(ctx.feedback_scores.get(c.recipe_id, 0), -6, 6) / 3
    affinity = favourite_affinity(c, ctx.favourites) if ctx.favourites else 0.0
    bmi_priority = 0.0
    if ctx.prioritise_weight_loss_meals:
        light = 1 - min(1.0, p.calories_kcal / max(1.0, ctx.calorie_target * 1.2))
        bmi_priority = 0.6 * min(1.0, _protein_density(p) / 0.3) + 0.4 * light
    balance = (1.0 if ctx.need_vegetable and c.has_vegetable else 0.0) + (
        1.0 if ctx.need_fruit and c.has_fruit else 0.0
    )
    return (
        w["nutrition_fit"] * nutrition_fit
        + w["protein_fit"] * protein_fit
        + w["goal_fit"] * goal_fit(p, ctx)
        + w["budget_fit"] * budget_fit
        - w["over_meal_budget"] * over_budget
        + w["feedback"] * feedback
        + w["favourite_similarity"] * affinity
        + w["bmi_priority"] * bmi_priority
        - w["repeat_penalty"] * ctx.weekly_counts.get(c.recipe_id, 0)
        - w["recent_penalty"] * (1.0 if c.recipe_id in ctx.recent_recipe_ids else 0.0)
        + w["balance"] * balance
    )


def rank_portions(portions: Iterable[Portion], ctx: RankingContext) -> list[RankedCandidate]:
    ranked = [RankedCandidate(portion=p, score=score_portion(p, ctx)) for p in portions]
    ranked.sort(key=lambda r: (-r.score, r.portion.candidate.recipe_id))
    return ranked

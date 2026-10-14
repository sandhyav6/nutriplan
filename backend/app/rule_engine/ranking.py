"""Stage 7 – ranking of already-eligible candidates (soft preferences only).

Score combines nutrition fit, budget fit and the user's weighted feedback
(``config.FEEDBACK_WEIGHTS``), plus Rule 6 (BMI > 25 favours weight-loss meals) and
Rule 8 (favourites promote nutritionally similar meals). Ties are broken by recipe id
so results are deterministic.

Implementation is scheduled for Milestone 2.
"""

from collections.abc import Iterable, Mapping

from app.rule_engine.types import MealCandidate, NutritionTarget, RankedCandidate

_PENDING = "Scheduled for Milestone 2 (rule engine) – see docs/development-roadmap.md"


def score_candidate(
    candidate: MealCandidate,
    target: NutritionTarget,
    feedback_scores: Mapping[int, int],
) -> float:
    raise NotImplementedError(_PENDING)


def rank_candidates(
    candidates: Iterable[MealCandidate],
    target: NutritionTarget,
    feedback_scores: Mapping[int, int],
) -> list[RankedCandidate]:
    raise NotImplementedError(_PENDING)

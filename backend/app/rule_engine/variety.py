"""Stage 8 – meal variety (REQ-4.2.6, Rule 7).

A recipe may appear at most ``config.MAX_REPEATS_PER_WEEK`` times per plan, and a
candidate too similar to a recently served meal is swapped for a nutritionally similar
alternative. Variety never overrides a hard constraint.

Implementation is scheduled for Milestone 2.
"""

from collections.abc import Mapping, Sequence

from app.rule_engine.types import MealCandidate

_PENDING = "Scheduled for Milestone 2 (rule engine) – see docs/development-roadmap.md"


def similarity(a: MealCandidate, b: MealCandidate) -> float:
    """Category/ingredient/nutrition similarity in the range 0..1."""
    raise NotImplementedError(_PENDING)


def passes_variety(
    candidate: MealCandidate,
    weekly_counts: Mapping[int, int],
    recent: Sequence[MealCandidate],
) -> bool:
    raise NotImplementedError(_PENDING)

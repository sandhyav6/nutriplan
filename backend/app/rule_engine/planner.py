"""Stage 9 – weekly planner and single-meal replacement.

``generate_weekly_plan`` will assemble 7 days x 4 slots from ranked, variety-checked
candidates and enforce the weekly budget (Rule 3: replace highest-cost meals first).
Slots with no safe candidate carry an explanation (REQ-4.2.8); hard constraints are
never broken to fill a slot.

Implementation is scheduled for Milestone 2 (planner) and Milestone 4 (replacement).
"""

from collections.abc import Mapping, Sequence

from app.rule_engine.types import MealCandidate, PlannedSlot, PlanResult, ProfileInput

_PENDING = "Scheduled for a later milestone – see docs/development-roadmap.md"


def generate_weekly_plan(
    profile: ProfileInput,
    candidates: Sequence[MealCandidate],
    feedback_scores: Mapping[int, int],
) -> PlanResult:
    raise NotImplementedError(_PENDING)


def find_replacement(
    profile: ProfileInput,
    plan: PlanResult,
    slot_to_replace: PlannedSlot,
    candidates: Sequence[MealCandidate],
    feedback_scores: Mapping[int, int],
) -> MealCandidate | None:
    """Return a constraint-satisfying alternative, or None if none exists (REQ-4.5.5)."""
    raise NotImplementedError(_PENDING)

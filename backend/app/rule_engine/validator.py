"""Stage 10 – independent constraint validator.

Re-checks a finished plan (or a single replacement) against the non-negotiable
constraints: diet, allergens/excluded foods, cooking time and weekly budget. It is kept
separate from candidate generation so it can also validate the output of the future
Phase 2 personalisation layer before anything reaches the user.

Implementation is scheduled for Milestone 2.
"""

from app.rule_engine.types import PlanResult, ProfileInput, ValidationResult

_PENDING = "Scheduled for Milestone 2 (rule engine) – see docs/development-roadmap.md"


def validate_plan(plan: PlanResult, profile: ProfileInput) -> ValidationResult:
    raise NotImplementedError(_PENDING)

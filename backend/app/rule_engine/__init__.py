"""Deterministic Phase 1 recommendation engine – STRUCTURE ONLY (Milestone 0).

The engine is pure: it receives plain data (``types.py``) and returns plain data.
It never touches the database or HTTP layer, so every rule is unit-testable.

Planned execution pipeline (Project Description §9, SRS Appendix B.2):

 1. Collect and validate profile inputs            -> types.ProfileInput
 2. Compute BMI and nutrition targets              -> nutrition.py
 3. Filter incompatible diets / declared allergens -> filters.py   (hard)
 4. Generate eligible meal candidates              -> filters.py
 5. Enforce cooking-time limits                    -> filters.py   (hard)
 6. Enforce per-meal and weekly budget             -> filters.py / planner.py (hard)
 7. Rank by nutrition fit, budget fit, feedback    -> ranking.py   (soft)
 8. Enforce meal variety (<= 2 repeats / week)     -> variety.py   (soft, never breaks hard rules)
 9. Assemble 7 days x 4 slots                      -> planner.py
10. Validate the completed plan                    -> validator.py (reusable after a Phase 2 layer)
11. Aggregate the grocery list                     -> services layer (Milestone 3)

Hard constraints (diet, allergies, budget, cooking time) are never relaxed to improve
ranking, variety or satisfaction. When nothing valid exists the engine returns an
explicit infeasibility explanation instead of an invalid recommendation.
"""

# CLAUDE.md – NutriPlan repository conventions

## Source of truth
* `docs/requirements/NutriPlan-SRS.docx` (SRS v1.0) is the Release 1.0 baseline;
  `docs/requirements/NutriPlan-Project-Description.docx` is the supporting reference.
  The `.md` files next to them are extracted copies for reading – never edit the `.docx` files.
* Do not silently change requirements. Record ambiguities and assumptions in
  `docs/requirements/open-decisions.md`; keep `requirements-matrix.md` up to date when a
  requirement is implemented or tested.
* Work milestone by milestone (`docs/development-roadmap.md`). Do not build features from a
  later milestone early, and never make unfinished features look functional – show a
  `DevelopmentNotice` (frontend) or return HTTP 501 (backend) instead.

## Scope guardrails
* Phase 1 only: deterministic, rule-based recommendations. **No** LLM/API calls, machine
  learning, LangChain, embeddings or vector databases.
* Hard constraints – dietary preference, allergens/excluded foods, cooking-time limit and
  weekly budget – are never relaxed for ranking, variety or satisfaction. When nothing valid
  exists, return an explicit explanation, never an unsafe recommendation.
* Every plan or replacement passes `app/rule_engine/validator.py` before it is stored or shown.
* No unnecessary services or frameworks (no Redis, Celery, Kubernetes, microservices).

## Backend (`backend/`, Python 3.14, FastAPI)
* Layering: `api/v1` (thin routers) → `services` → `repositories` / `rule_engine`.
  Routers hold no SQL or business rules; the rule engine imports nothing from `fastapi`,
  `app.api` or `app.db.session` and operates on dataclasses in `rule_engine/types.py`.
* Rule-engine numbers live in `rule_engine/config.py` with a SOURCE or TBD comment – no
  unexplained magic numbers. Tie-breaks must be deterministic (e.g. by id).
* Settings only through `app.core.config.get_settings()`; secrets only from environment.
* Errors use the shared shape `{"error": {"code", "message", "details?"}}` (`core/errors.py`).
* Schema changes require an Alembic migration (`python -m alembic revision --autogenerate`),
  reviewed by hand; never use `create_all` at startup. Keep the naming convention in
  `db/base.py`. Money is `Numeric(10, 2)` in INR.
* Every private query filters by the authenticated user; admin routes depend on
  `require_admin`. Registration must never accept a role.
* Style: `ruff check .` and `ruff format .` (line length 100), full type hints.
* Tests: `pytest`; PostgreSQL integration tests are marked `integration` and skip without
  `TEST_DATABASE_URL`.

## Frontend (`frontend/`, React + TypeScript + Vite + Tailwind v4)
* Structure: `app/` (router), `pages/` (one component per route), `features/<feature>/`,
  `components/ui` (primitives), `components/layout`, `hooks/`, `lib/`, `types/`.
* All HTTP goes through `src/lib/apiClient.ts` (base `/api/v1`, proxied by Vite). No
  hard-coded hosts in components.
* Use the design tokens in `src/index.css` (`canvas`, `surface`, `ink`, `brand-*`, …) rather
  than ad-hoc colours. Keep pages keyboard-accessible with visible focus and proper landmarks.
* Never display fabricated nutrition, price or user data as real.
* Checks: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.
* React Hook Form + Zod arrive in M1 (forms) and Recharts in M6 (dashboard).

## Git
* Do not commit or push automatically; the maintainer commits. No secrets or `.env` files in
  Git.

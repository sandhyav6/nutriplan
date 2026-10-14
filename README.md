# NutriPlan – Adaptive Meal Planning Based on Lifestyle

NutriPlan is a web application that generates personalised **weekly meal plans** and a
consolidated **grocery list** from a user's dietary preference, declared allergies, health
goal (weight loss, muscle gain, maintenance), weekly budget in ₹ and available cooking time.
Users give feedback (like / dislike / skip / favourite) that adjusts future recommendations,
can replace a single meal without breaking their constraints, and see a dashboard of weekly
calories and spending. Administrators maintain the food, recipe, nutrition and category data.

Team: Anvita Arun (24BCE1173), Sandhya Venkatesh (24BCE1042), Saadhvi H (24BCE1987) – VIT Chennai.

* **Release 1.0 / Phase 1 (this repository):** a deterministic, rule-based recommendation
  engine whose decisions are explainable, reproducible and validated against non-negotiable
  constraints.
* **Phase 2 (future, not implemented):** an LLM personalisation layer on rule-generated
  candidates, followed by the same independent constraint validator.

Requirements: [SRS v1.0](docs/requirements/NutriPlan-SRS.docx) (baseline) and the
[Detailed Project Description](docs/requirements/NutriPlan-Project-Description.docx), with
Markdown extracts alongside them.

## Current status – Milestone 0 (project foundation)

| Area | Implemented now | Planned |
| --- | --- | --- |
| Backend | FastAPI app, `/api/v1/health` (with DB check), settings, JSON logging, consistent errors, CORS, Swagger at `/docs` | Feature APIs from M1 |
| Database | SQLAlchemy models + initial Alembic migration for all core entities; seeded meal categories and allergen list | Catalogue data (M2) |
| Rule engine | Package structure, typed interfaces, documented constants | Algorithms (M3–M5) |
| Frontend | React + TS + Tailwind layout, routing for all 10 screens, live API status indicator | Working forms and data (M1+) |
| Quality | Pytest, Vitest + Testing Library, Ruff, ESLint, TypeScript, GitHub Actions CI | Grows each milestone |

Not implemented yet (by design): authentication, profile saving, nutrition calculations,
plan generation, grocery aggregation, feedback, meal replacement, dashboard statistics and
admin CRUD. Screens for these show an **"In development"** notice and disabled controls.
See the [development roadmap](docs/development-roadmap.md).

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, TypeScript 6.0, Vite 8, Tailwind CSS 4 (`@tailwindcss/vite`), React Router 8, typed Fetch client, Vitest 5 + React Testing Library, ESLint 10 |
| Backend | Python 3.14, FastAPI, Pydantic v2 + pydantic-settings, SQLAlchemy 2.x, Alembic, psycopg 3, Uvicorn, Pytest + HTTPX, Ruff |
| Database | PostgreSQL 17 (Docker Compose) |
| CI | GitHub Actions (backend with a PostgreSQL service container; frontend lint/typecheck/test/build) |

Exact backend versions are pinned in `backend/requirements.txt`; frontend versions are locked
in `frontend/package-lock.json`. React Hook Form + Zod are added in M1 and Recharts in M6 (see
[OD-14](docs/requirements/open-decisions.md)).

## Repository structure

```
nutriplan/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # versioned REST routers (health now)
│   │   ├── core/            # settings, logging, error handling
│   │   ├── db/              # declarative base, engine/session dependency
│   │   ├── models/          # SQLAlchemy entities
│   │   ├── schemas/         # Pydantic contracts
│   │   ├── repositories/    # persistence (from M1)
│   │   ├── services/        # use cases (from M1)
│   │   ├── rule_engine/     # deterministic recommendation engine (interfaces now)
│   │   └── main.py          # FastAPI entry point
│   ├── alembic/             # migrations
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml       # Ruff + pytest config
├── frontend/
│   └── src/{app,components/{ui,layout},pages,features,hooks,lib,types,test}
├── docs/
│   ├── requirements/        # SRS + Description (.docx + .md), traceability, open decisions
│   ├── architecture/        # overview, database design
│   └── development-roadmap.md
├── docker/postgres/init/    # creates the test database on first start
├── scripts/extract_docx.py  # regenerates the .md requirement extracts
├── compose.yaml
├── .env.example             # Docker Compose variables
└── .github/workflows/ci.yml
```

## Prerequisites

* **Python 3.14** (`py -3.14` on Windows)
* **Node.js 22 LTS** (≥ 20.19) and npm
* **Docker Desktop** (for PostgreSQL)
* Git

## Setup (Windows PowerShell)

Run from the repository root unless noted.

```powershell
# 1. Environment files (local development values only – change the password)
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env.local   # optional

# 2. Start PostgreSQL (127.0.0.1:5433)
docker compose up -d db
docker compose ps          # wait until "healthy"

# 3. Backend
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

macOS / Linux differences: `cp` instead of `Copy-Item`, `python3.14 -m venv .venv` and
`source .venv/bin/activate`.

The password in `.env` and the one inside `DATABASE_URL` / `TEST_DATABASE_URL` in
`backend/.env` must match.

## Development URLs

| What | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| API health | http://127.0.0.1:8000/api/v1/health (or http://localhost:5173/api/v1/health via the proxy) |
| Swagger UI | http://127.0.0.1:8000/docs |
| PostgreSQL | `127.0.0.1:5433`, database `nutriplan` (tests: `nutriplan_test`) |

## Database migrations

```powershell
cd backend
python -m alembic upgrade head                       # apply
python -m alembic downgrade -1                       # roll back one revision
python -m alembic revision --autogenerate -m "msg"   # after changing models – review the file!
python -m alembic check                              # models and migrations in sync?
python -m alembic -x db_url=postgresql+psycopg://... upgrade head   # another database
```

## Tests and checks

```powershell
# Backend (inside backend/, venv active)
python -m ruff check .
python -m ruff format --check .
python -m pytest                    # integration tests run when TEST_DATABASE_URL is set

# Frontend (inside frontend/)
npm run lint
npm run typecheck
npm test
npm run build
```

CI runs all of the above on every push to `main` and on pull requests.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `docker compose` cannot connect to `dockerDesktopLinuxEngine` | Start Docker Desktop and wait until it reports *Engine running*. |
| `Set POSTGRES_USER in .env` | Copy `.env.example` to `.env` in the repository root. |
| Port 5433 already in use | Change `POSTGRES_HOST_PORT` in `.env` and the port in `backend/.env`. |
| `password authentication failed` | Passwords in `.env` and `backend/.env` differ, or the volume was created with an old password: `docker compose down -v` (deletes local data) and start again. |
| `DATABASE_URL is not configured` | Create `backend/.env` from `backend/.env.example`, and run commands from inside `backend/`. |
| Health shows `database: unavailable` | PostgreSQL is not running or the URL is wrong; the API itself is up. |
| Frontend shows **API offline** | Start the backend on port 8000 (or set `VITE_API_PROXY_TARGET`). |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or call `.\.venv\Scripts\python.exe` directly. |
| Test database missing | It is created only on the first volume initialisation; run `docker compose exec db createdb -U nutriplan nutriplan_test`. |

## Documentation

* [Architecture overview](docs/architecture/overview.md)
* [Database design](docs/architecture/database-design.md)
* [Requirements traceability matrix](docs/requirements/requirements-matrix.md)
* [Open decisions and assumptions](docs/requirements/open-decisions.md)
* [Development roadmap](docs/development-roadmap.md)
* [Repository conventions (CLAUDE.md)](CLAUDE.md)

> Nutrition values shown by NutriPlan are estimates and not medical advice.

# NutriPlan – Adaptive Meal Planning Based on Lifestyle

NutriPlan is a web application that generates personalised **weekly meal plans** and a
consolidated **grocery list** from a user's dietary preference, declared allergies, health
goal (weight loss, muscle gain, maintenance), weekly budget in ₹ and available cooking time.
Users give feedback (like / dislike / skip / favourite) that adjusts future recommendations,
can replace a single meal without breaking their constraints, and see a dashboard of weekly
calories and spending. Administrators maintain the food, recipe, nutrition and category data.


* **Release 1.0 / Phase 1 (this repository):** a deterministic, rule-based recommendation
  engine whose decisions are explainable, reproducible and validated against non-negotiable
  constraints.
* **Phase 2 (future, not implemented):** an LLM personalisation layer on rule-generated
  candidates, followed by the same independent constraint validator.

Requirements: [SRS v1.0](docs/requirements/NutriPlan-SRS.docx) (baseline) and the
[Detailed Project Description](docs/requirements/NutriPlan-Project-Description.docx), with
Markdown extracts alongside them.

## Current status – Release 1.0 feature-complete (Milestones 0–6)

| Area | What works |
| --- | --- |
| Accounts | Register, log in, log out; Argon2id password hashing; HttpOnly session cookie + CSRF double-submit token; roles `user` / `admin` (admins are created by a CLI command only) |
| Profile | Age, gender, height, weight, activity, dietary preference, health goal, weekly budget (₹), cooking-time limit, allergies and excluded foods; inline validation; BMI, daily calorie and protein target, per-meal budget |
| Weekly plan | Deterministic 7 days × 4 slots from the rule engine. Diet, allergens/excluded foods, cooking time and weekly budget are hard constraints; portion sizes (0.75–2 servings) meet the calorie target; empty slots and an unaffordable budget are explained; every plan passes the independent validator |
| Grocery list | Aggregated, de-duplicated ingredients in readable units (g/kg, ml/L, pieces), grouped by food group, estimated cost vs budget; regenerated automatically after a replacement |
| Feedback | Like / dislike / skip / favourite per meal; weighted scores change future ranking; favourites boost similar meals |
| Replacement | Swap one meal for another that keeps every hard constraint, the weekly budget and ±20 % calories – or get an explanation that none exists |
| Dashboard | Weekly and daily calories vs target (Recharts), estimated spend vs budget, meal statistics, favourites |
| Admin panel | CRUD for foods, nutrition values and recipes (ingredients, prep time; nutrition and cost recalculated automatically); rename the four fixed meal categories |
| Help | In-app getting-started guide, FAQ and administrator guide at `/help` |
| Deployment | One production container (`Dockerfile`) serving the API and the built frontend on one origin |

Phase 2 (LLM personalisation) is intentionally **not** implemented. The bundled dataset
(72 foods, 100 recipes) is **illustrative development data** – approximate nutrition values
and indicative ₹ prices, not verified data ([OD-15](docs/requirements/open-decisions.md)).
Administrators can replace it through the admin panel.

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, TypeScript 6.0, Vite 8, Tailwind CSS 4 (`@tailwindcss/vite`), React Router 8, React Hook Form + Zod, Recharts (lazy-loaded), typed Fetch client, Vitest 5 + React Testing Library, ESLint 10 |
| Backend | Python 3.14, FastAPI, Pydantic v2 + pydantic-settings, SQLAlchemy 2.x, Alembic, psycopg 3, argon2-cffi, Uvicorn, Pytest + HTTPX, Ruff |
| Database | PostgreSQL 17 (Docker Compose) |
| Deployment | Multi-stage `Dockerfile` (Node 22 build → Python 3.14 slim runtime, non-root) |
| CI | GitHub Actions (backend with a PostgreSQL service container; frontend lint/typecheck/test/build; production image build) |

Exact backend versions are pinned in `backend/requirements.txt`; frontend versions are locked
in `frontend/package-lock.json`.

## Repository structure

```
nutriplan/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # thin REST routers: health, auth, profile, reference, plans, admin
│   │   ├── core/            # settings, logging, errors, security, CSRF, dependencies
│   │   ├── db/              # declarative base, engine/session dependency
│   │   ├── models/          # SQLAlchemy entities
│   │   ├── schemas/         # Pydantic contracts
│   │   ├── repositories/    # persistence
│   │   ├── services/        # use cases: auth, profile, catalogue, plans, grocery, feedback, dashboard
│   │   ├── rule_engine/     # deterministic recommendation engine (pure – no FastAPI / DB)
│   │   ├── seed/            # illustrative food & recipe dataset
│   │   ├── cli.py           # create-admin, seed-catalogue
│   │   └── main.py          # FastAPI entry point (also serves the built frontend in production)
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
├── docker/app/entrypoint.sh # production container: migrate, then start Uvicorn
├── Dockerfile               # production image (API + built frontend)
├── start.cmd / setup.cmd    # one-command start / setup without Docker
├── scripts/
│   ├── setup-local.ps1      # one-time setup without Docker (SQLite) – via setup.cmd
│   ├── start-local.ps1      # setup if needed, start backend + frontend, open browser – via start.cmd
│   └── extract_docx.py      # regenerates the .md requirement extracts
├── compose.yaml
├── .env.example             # Docker Compose variables
└── .github/workflows/ci.yml
```

## Prerequisites

* **Python 3.14** (`py -3.14` on Windows)
* **Node.js 22 LTS** (≥ 20.19) and npm
* Git
* *Optional:* **Docker Desktop** – only for the PostgreSQL setup below. **Docker is not
  required** to run, develop or test NutriPlan.

## Quick start without Docker (recommended on Windows)

Uses a local SQLite database file, so nothing else needs to be installed (OD-22). From the
repository root in PowerShell (or double-click `start.cmd` in Explorer):

```powershell
.\start.cmd
```

That one command:

1. sets the project up on first use (`backend\.venv`, Python and npm packages, `backend\.env`);
2. creates the database (folder included), applies the migrations and loads the illustrative
   food & recipe dataset – both are skipped when already done;
3. starts the **backend** in its own window and waits until `/api/v1/health` answers;
4. starts the **frontend** in its own window and **opens your browser** at it.

Close the two "NutriPlan" windows to stop. If port 8000 or 5173 is busy, the next free port is
used automatically and printed.

| Command | What it does |
| --- | --- |
| `.\start.cmd` | Development mode (hot reload) – the browser opens at http://localhost:5173 |
| `.\start.cmd -Production` | Builds the frontend and serves API + frontend from **one** process, like the Docker image – http://localhost:8000 |
| `.\start.cmd -Port 8080` / `-NoBrowser` | Fixed backend port / don't open the browser |
| `.\setup.cmd` | Setup only (`start.cmd` runs it automatically on first use) |

The scripts behind these are `scripts\start-local.ps1` and `scripts\setup-local.ps1`. The
database lives in `%LOCALAPPDATA%\NutriPlan\nutriplan.db` – outside OneDrive, because syncing a
live database file can corrupt it. If that folder is not writable, the scripts use
`backend\.data\` instead and update `backend\.env`. To start over with an empty database, close
the app and delete the `.db` file; the next `start.cmd` recreates it.

PostgreSQL stays the production and CI database. Everything in the app works the same on
SQLite; the PostgreSQL-specific checks run automatically in GitHub Actions on every push.

## Setup with PostgreSQL in Docker (optional)

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
python -m app.cli seed-catalogue      # illustrative foods & recipes (skipped if foods exist)

# Optional: an administrator (credentials come from environment variables only)
$env:NUTRIPLAN_ADMIN_EMAIL = "admin@example.com"
$env:NUTRIPLAN_ADMIN_PASSWORD = "<choose a strong password>"
python -m app.cli create-admin        # creates the admin, or promotes an existing account
Remove-Item Env:NUTRIPLAN_ADMIN_PASSWORD

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
`backend/.env` must match. (If you already ran `setup-local.ps1`, replace its two SQLite URLs
in `backend/.env` with the PostgreSQL ones from `backend/.env.example`.)

**Native PostgreSQL without Docker** also works: install PostgreSQL 17, create the databases
`nutriplan` and `nutriplan_test`, and put their URLs (port 5432) in `backend/.env`.

### Using the app

1. Open http://localhost:5173, **Register**, and complete your **Profile** – NutriPlan shows
   your BMI, daily calorie and protein target and per-meal budget.
2. **Meal Plan → Generate weekly plan** creates the 7 × 4 plan. Slots with no safe meal, or a
   budget that cannot be met, are explained instead of being filled with unsafe meals.
3. Open a meal to see ingredients and nutrition, give **feedback** or **replace** it.
4. **Grocery List** shows the aggregated shopping list; **Dashboard** shows calories, spend and
   statistics. The administrator also sees **Admin** for maintaining the catalogue.

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

## Deploy online (Render, free tier)

The web service runs on Render; the database runs on Neon, whose free PostgreSQL plan does
not expire. `render.yaml` is the Render Blueprint for the web service.

1. Push the repository to GitHub.
2. On https://neon.tech sign in, create a project (PostgreSQL 17, a region close to your
   Render region) and copy the **connection string** (`postgresql://…?sslmode=require`).
3. On https://render.com sign in with GitHub, choose **New → Blueprint**, select the
   repository and click **Apply**.
4. When asked, paste the Neon string as `DATABASE_URL` and enter `NUTRIPLAN_ADMIN_EMAIL` and
   `NUTRIPLAN_ADMIN_PASSWORD` (at least 8 characters with a letter and a number).
5. Wait for the first build (about 5–10 minutes), then open the `https://nutriplan-….onrender.com`
   URL shown on the service.

On every start the container applies migrations, loads the illustrative dataset if the
catalogue is empty (`SEED_CATALOGUE=1`) and creates or updates the administrator from the two
variables – no shell access is needed. `postgres://` / `postgresql://` URLs are accepted as
given. Free Render services sleep after about 15 minutes without traffic, so the first request
afterwards takes up to a minute; Neon pauses idle databases and resumes them automatically.

## Production build (Docker)

The `Dockerfile` builds the frontend, installs only the runtime Python dependencies and runs
FastAPI as a non-root user. FastAPI serves the built React app (`FRONTEND_DIST_DIR`) and the
API from **one origin**, so no CORS or proxy setup is needed. On start the container applies
migrations (set `RUN_MIGRATIONS=0` to skip) and then starts Uvicorn on `PORT` (default 8000).

Try it locally against the Compose PostgreSQL (http://localhost:8000):

```powershell
docker compose --profile prod up --build -d
docker compose exec app python -m app.cli seed-catalogue
docker compose exec -e NUTRIPLAN_ADMIN_EMAIL=admin@example.com -e NUTRIPLAN_ADMIN_PASSWORD=<password> app python -m app.cli create-admin
```

Or build and run the image on its own:

```powershell
docker build -t nutriplan .
docker run -p 8000:8000 -e DATABASE_URL=postgresql+psycopg://user:pass@dbhost:5432/nutriplan nutriplan
```

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | **Required.** PostgreSQL URL (`postgresql+psycopg://…`); percent-encode special characters in the password |
| `ENVIRONMENT` | `production` in the image → cookies are `Secure` |
| `COOKIE_SECURE` | Overrides the cookie `Secure` flag (Compose sets `false` for the plain-HTTP localhost trial) |
| `PORT` / `RUN_MIGRATIONS` / `LOG_LEVEL` | Listen port (8000) / apply migrations on start (1) / log level (INFO) |
| `SEED_CATALOGUE` | `1` loads the illustrative dataset on start if no foods exist (default `0`) |
| `NUTRIPLAN_ADMIN_EMAIL` / `NUTRIPLAN_ADMIN_PASSWORD` | If both are set, the administrator is created or updated on start |
| `FORWARDED_ALLOW_IPS` | Address of the TLS-terminating reverse proxy trusted for `X-Forwarded-*` |

In production, run the container behind HTTPS (SRS §5.3) and leave `COOKIE_SECURE` unset.
**Without Docker**, `.\start.cmd -Production` gives the same single-origin setup
(it runs `npm run build` and starts Uvicorn with `FRONTEND_DIST_DIR=frontend/dist`). The image
itself is built and checked by CI on every push.

## Tests and checks

```powershell
# Backend (inside backend/, venv active)
python -m ruff check .
python -m ruff format --check .
python -m pytest                    # everything; integration tests run when TEST_DATABASE_URL is set
python -m pytest -m integration     # only the migration/full-flow integration tests

# Frontend (inside frontend/)
npm run lint
npm run typecheck
npm test
npm run build
```

Integration tests run against whatever `TEST_DATABASE_URL` points to: the SQLite test file
written by `setup-local.ps1` locally, PostgreSQL in Docker if you use it, and **always
PostgreSQL in CI**. CI runs all of the above, plus the Docker image build, on every push to
`main` and on pull requests – so PostgreSQL and Docker are verified even if you never install
them.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `docker compose` cannot connect to `dockerDesktopLinuxEngine` | Start Docker Desktop and wait until it reports *Engine running* – or skip Docker entirely: [Quick start without Docker](#quick-start-without-docker-recommended-on-windows). |
| `running scripts is disabled on this system` | Use `.\start.cmd` / `.\setup.cmd` – they bypass the execution policy for these scripts only. |
| `'start.cmd' is not recognized` | In PowerShell, type `.\start.cmd` (with `.\`) from the repository root. |
| `unable to open database file` | Run `.\start.cmd` again – it creates the database folder (or falls back to `backend\.data`). Check that `DATABASE_URL` in `backend\.env` points to a folder you can write to. |
| Browser shows **API offline** | Read the error in the "NutriPlan backend" window, fix it, and run `.\start.cmd` again. |
| `database is locked` (SQLite) | Another NutriPlan process is using the file – close other running backend windows. |
| Port 8000 or 5173 already in use | `start.cmd` picks the next free port automatically, or set one with `.\start.cmd -Port 8080`. |
| `Set POSTGRES_USER in .env` | Copy `.env.example` to `.env` in the repository root. |
| Port 5433 already in use | Change `POSTGRES_HOST_PORT` in `.env` and the port in `backend/.env`. |
| `password authentication failed` | Passwords in `.env` and `backend/.env` differ, or the volume was created with an old password: `docker compose down -v` (deletes local data) and start again. |
| `DATABASE_URL is not configured` | Run `.\setup.cmd` (or create `backend/.env` from `backend/.env.example`), and run commands from inside `backend/`. |
| Health shows `database: unavailable` | The database in `DATABASE_URL` is not reachable (PostgreSQL not running or wrong URL); the API itself is up. |
| Frontend shows **API offline** | Start the backend on port 8000 (or set `VITE_API_PROXY_TARGET`). |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or call `.\.venv\Scripts\python.exe` directly. |
| Generating a plan says the catalogue is empty | Run `python -m app.cli seed-catalogue`, or add recipes in the admin panel. |
| "Budget cannot be met" | The weekly budget is below the cheapest valid plan; the message shows the minimum. Raise the budget or allow more cooking time. |
| No **Admin** link | Only accounts created/promoted with `python -m app.cli create-admin` are administrators; log in again after promoting. |
| Test database missing | It is created only on the first volume initialisation; run `docker compose exec db createdb -U nutriplan nutriplan_test`. |

## Documentation

* [Architecture overview](docs/architecture/overview.md)
* [Database design](docs/architecture/database-design.md)
* [Requirements traceability matrix](docs/requirements/requirements-matrix.md)
* [Open decisions and assumptions](docs/requirements/open-decisions.md)
* [Development roadmap](docs/development-roadmap.md)
* In-app user help, FAQ and administrator guide: `/help` (OD-19)
* [Repository conventions (CLAUDE.md)](CLAUDE.md)

> Nutrition values shown by NutriPlan are estimates and not medical advice.

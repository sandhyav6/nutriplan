# Production image: one container serving the FastAPI API and the built React app on one origin.
#
#   docker build -t nutriplan .
#   docker run -p 8000:8000 -e DATABASE_URL=postgresql+psycopg://user:pass@host:5432/nutriplan nutriplan
#
# Or with the bundled PostgreSQL:  docker compose --profile prod up --build
# Configuration comes only from environment variables (see backend/.env.example); no secrets
# are baked into the image.

# --- Stage 1: build the frontend -----------------------------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python runtime ---------------------------------------------------------------
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=production \
    FRONTEND_DIST_DIR=/app/frontend-dist \
    PORT=8000

WORKDIR /app

# Runtime dependencies only: everything above the "Development / testing" block.
COPY backend/requirements.txt ./requirements.txt
RUN sed '/^# --- Development/,$d' requirements.txt > requirements-runtime.txt \
    && pip install -r requirements-runtime.txt \
    && rm requirements.txt requirements-runtime.txt

COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY --from=frontend /build/dist ./frontend-dist
COPY docker/app/entrypoint.sh /usr/local/bin/nutriplan-entrypoint
RUN chmod 0755 /usr/local/bin/nutriplan-entrypoint \
    && useradd --system --uid 10001 --no-create-home nutriplan

USER nutriplan
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/v1/health', timeout=4)" || exit 1

ENTRYPOINT ["nutriplan-entrypoint"]

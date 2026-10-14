#!/bin/sh
# Container entry point: apply migrations (unless RUN_MIGRATIONS=0), then start Uvicorn.
# Extra arguments are passed to Uvicorn, e.g. `--workers 2`.
set -eu

if [ -z "${DATABASE_URL:-}" ]; then
    echo "DATABASE_URL is not set - refusing to start." >&2
    exit 1
fi

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    python -m alembic upgrade head
fi

# --proxy-headers trusts X-Forwarded-* only from FORWARDED_ALLOW_IPS (default 127.0.0.1);
# set it to the address of your TLS-terminating reverse proxy.
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers "$@"

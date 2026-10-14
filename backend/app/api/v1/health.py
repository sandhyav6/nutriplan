"""GET /api/v1/health – liveness of the API plus a database connectivity check."""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from app import __version__
from app.core.config import Settings, get_settings
from app.db.session import check_database_connection
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    database_ok = await run_in_threadpool(check_database_connection)
    return HealthResponse(
        status="ok" if database_ok else "degraded",
        service=settings.app_name,
        version=__version__,
        environment=settings.environment,
        database="ok" if database_ok else "unavailable",
    )

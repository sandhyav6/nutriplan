"""FastAPI application entry point.

Run from the backend/ directory:
    python -m uvicorn app.main:app --reload

In production the built React app (``frontend/dist`` or ``FRONTEND_DIST_DIR``) is served by
the same process, so the browser talks to a single HTTPS origin.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.csrf import csrf_middleware
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, request_logging_middleware


def _mount_frontend(app: FastAPI, dist: Path, api_prefix: str) -> None:
    index = dist / "index.html"
    if not index.is_file():
        return
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        # Unknown /api paths must still 404 as JSON, not return the SPA.
        if path.startswith(api_prefix.strip("/")):
            from fastapi import HTTPException

            raise HTTPException(404, "Not Found")
        candidate = (dist / path).resolve()
        if path and candidate.is_file() and dist.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(index)  # client-side routing


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "NutriPlan – Adaptive Meal Planning Based on Lifestyle. Release 1.0 (Phase 1): "
            "deterministic rule-based meal plans, grocery lists, feedback, dashboard and admin."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
    )
    app.middleware("http")(csrf_middleware)
    app.middleware("http")(request_logging_middleware)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    dist = Path(settings.frontend_dist_dir) if settings.frontend_dist_dir else None
    if dist is not None:
        _mount_frontend(app, dist, settings.api_v1_prefix)
    return app


app = create_app()

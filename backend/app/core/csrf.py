"""CSRF protection – double-submit cookie (OD-12).

Every state-changing request (POST/PUT/PATCH/DELETE) to the API must send the value of
the ``np_csrf`` cookie in the ``X-CSRF-Token`` header. A cross-site page cannot read the
cookie, so it cannot forge the header. ``GET /api/v1/auth/csrf`` issues the cookie.
"""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import error_body
from app.core.security import tokens_match

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


async def csrf_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    settings = get_settings()
    if request.method in UNSAFE_METHODS and request.url.path.startswith(settings.api_v1_prefix):
        cookie = request.cookies.get(settings.csrf_cookie_name)
        header = request.headers.get(settings.csrf_header_name)
        if not tokens_match(cookie, header):
            return JSONResponse(
                status_code=403,
                content=error_body(
                    "csrf_failed",
                    "Missing or invalid CSRF token. Refresh the page and try again.",
                ),
            )
    return await call_next(request)


def set_csrf_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.csrf_cookie_name,
        token,
        httponly=False,  # must be readable by the SPA to copy into the header
        secure=settings.use_secure_cookies,
        samesite="lax",
        path="/",
    )

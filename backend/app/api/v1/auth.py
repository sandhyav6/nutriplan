"""Authentication endpoints (UC-01 Register, UC-02 Login, UC-03 Logout)."""

from fastapi import APIRouter, Request, Response, status

from app.core.config import get_settings
from app.core.csrf import set_csrf_cookie
from app.core.deps import CurrentUser, DbSession
from app.core.security import generate_token
from app.repositories import profiles as profile_repo
from app.schemas.auth import CsrfOut, LoginRequest, RegisterRequest, SessionOut, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _session_out(db: DbSession, user) -> SessionOut:  # type: ignore[no-untyped-def]
    return SessionOut(
        user=UserOut.model_validate(user),
        has_profile=profile_repo.get_for_user(db, user.id) is not None,
    )


@router.get("/csrf", response_model=CsrfOut, summary="Issue a CSRF token cookie")
def csrf(request: Request, response: Response) -> CsrfOut:
    token = request.cookies.get(get_settings().csrf_cookie_name) or generate_token()
    set_csrf_cookie(response, token)
    return CsrfOut(csrf_token=token)


@router.post("/register", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: DbSession, response: Response) -> SessionOut:
    user = auth_service.register(db, data)
    auth_service.start_session(db, user, response)
    return _session_out(db, user)


@router.post("/login", response_model=SessionOut)
def login(data: LoginRequest, db: DbSession, response: Response) -> SessionOut:
    user = auth_service.authenticate(db, data)
    auth_service.start_session(db, user, response)
    return _session_out(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: DbSession, response: Response) -> Response:
    auth_service.end_session(db, request.cookies.get(get_settings().session_cookie_name), response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=SessionOut)
def me(user: CurrentUser, db: DbSession) -> SessionOut:
    return _session_out(db, user)

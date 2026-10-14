"""Profile endpoints (REQ-4.1.3 – REQ-4.1.5). A user can only ever access their own profile."""

from fastapi import APIRouter, Response, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.profile import ProfileIn, ProfileOut
from app.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
def get_profile(user: CurrentUser, db: DbSession) -> ProfileOut:
    return profile_service.to_profile_out(profile_service.get_profile(db, user))


@router.put("", response_model=ProfileOut)
def save_profile(
    data: ProfileIn, user: CurrentUser, db: DbSession, response: Response
) -> ProfileOut:
    profile, created = profile_service.save_profile(db, user, data)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return profile_service.to_profile_out(profile)

"""Aggregates all v1 routers.

Feature routers (auth, profiles, meal plans, grocery lists, feedback, dashboard,
admin) are added in later milestones – see docs/development-roadmap.md.
"""

from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)

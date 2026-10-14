"""Aggregates all v1 routers."""

from fastapi import APIRouter

from app.api.v1 import admin, auth, health, plans, profile, reference

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(reference.router)
api_router.include_router(plans.router)
api_router.include_router(admin.router)

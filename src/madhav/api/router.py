"""Centralized API router registration."""

from fastapi import APIRouter, FastAPI

from madhav.ai.api.routes import router as ai_router
from madhav.api.health import router as health_router
from madhav.identity.api.routes import router as identity_router
from madhav.models.api.routes import router as models_router


def register_routers(app: FastAPI) -> None:
    """Register top-level and versioned API routers with the FastAPI app."""
    # Top level system foundation endpoints
    app.include_router(health_router)

    # API v1 Router prefix foundation
    v1_router = APIRouter(prefix="/api/v1")
    v1_router.include_router(identity_router)
    v1_router.include_router(ai_router)
    v1_router.include_router(models_router)
    app.include_router(v1_router)

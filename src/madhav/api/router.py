"""Centralized API router registration."""

from fastapi import APIRouter, FastAPI

from madhav.api.health import router as health_router


def register_routers(app: FastAPI) -> None:
    """Register top-level and versioned API routers with the FastAPI app."""
    # Top level system foundation endpoints
    app.include_router(health_router)

    # API v1 Router prefix foundation for future modules
    v1_router = APIRouter(prefix="/api/v1")
    app.include_router(v1_router)

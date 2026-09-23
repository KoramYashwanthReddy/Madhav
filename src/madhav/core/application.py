"""Application factory for MADHAV platform foundation."""

from fastapi import FastAPI

from madhav.api.router import register_routers
from madhav.core.error_handlers import register_exception_handlers
from madhav.core.lifecycle import lifespan
from madhav.core.logging import setup_logging
from madhav.core.request_id import RequestIDMiddleware
from madhav.version import APP_NAME, VERSION


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    # 1. Configure structured logging
    setup_logging()

    # 2. Instantiate FastAPI with application metadata and lifespan
    app = FastAPI(
        title=APP_NAME,
        version=VERSION,
        description="MADHAV Personal AI System — Platform Foundation",
        lifespan=lifespan,
    )

    # 3. Add middleware
    app.add_middleware(RequestIDMiddleware)

    # 4. Register exception handlers
    register_exception_handlers(app)

    # 5. Register API routes
    register_routers(app)

    return app

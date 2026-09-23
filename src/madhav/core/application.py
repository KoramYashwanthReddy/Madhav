"""Application factory for MADHAV platform foundation."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from madhav.api.router import register_routers
from madhav.config.settings import Settings, get_settings
from madhav.core.error_handlers import register_exception_handlers
from madhav.core.lifecycle import lifespan
from madhav.core.logging import setup_logging
from madhav.core.request_id import RequestIDMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application instance using Settings."""
    if settings is None:
        settings = get_settings()

    # 1. Configure structured logging from settings
    setup_logging(
        level=str(settings.logging.level),
        json_format=settings.logging.json_format,
    )

    # 2. Determine documentation availability from API settings and feature flags
    docs_enabled = settings.api.docs_enabled and settings.features.api_docs
    docs_url = f"{settings.api.prefix}/{settings.api.version}/docs" if docs_enabled else None
    redoc_url = f"{settings.api.prefix}/{settings.api.version}/redoc" if docs_enabled else None
    openapi_url = (
        f"{settings.api.prefix}/{settings.api.version}/openapi.json"
        if settings.api.openapi_enabled
        else None
    )

    # 3. Instantiate FastAPI with application metadata, docs configuration, and lifespan
    app = FastAPI(
        title=settings.application.name,
        version=settings.application.version,
        description="MADHAV Personal AI System",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        debug=settings.application.debug,
        lifespan=lifespan,
    )

    app.state.settings = settings

    # 4. Add CORS middleware if enabled
    if settings.cors.enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors.allowed_origins,
            allow_credentials=settings.cors.allow_credentials,
            allow_methods=settings.cors.allowed_methods,
            allow_headers=settings.cors.allowed_headers,
        )

    # 5. Add Request ID correlation middleware
    app.add_middleware(RequestIDMiddleware)

    # 6. Register exception handlers
    register_exception_handlers(app)

    # 7. Register API routes
    register_routers(app)

    return app

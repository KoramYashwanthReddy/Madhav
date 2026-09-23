"""Health, readiness, and service identity endpoints."""

from typing import Any

from fastapi import APIRouter, Request

from madhav.common.interfaces import HealthCheckProvider
from madhav.config.loader import get_settings
from madhav.core.request_id import get_request_id
from madhav.core.responses import APIResponse

router = APIRouter(tags=["Platform Foundation"])

_readiness_providers: list[HealthCheckProvider] = []


def register_readiness_provider(provider: HealthCheckProvider) -> None:
    """Register a component health provider for system readiness checks."""
    _readiness_providers.append(provider)


@router.get("/", response_model=APIResponse[dict[str, str]])
async def get_root(request: Request) -> APIResponse[dict[str, str]]:
    """Root endpoint returning service identity."""
    settings = getattr(request.app.state, "settings", get_settings())
    return APIResponse(
        success=True,
        data={
            "name": settings.application.name,
            "service": settings.application.service_name,
            "version": settings.application.version,
            "environment": str(settings.application.environment),
            "message": "MADHAV platform is running.",
        },
        request_id=get_request_id(),
    )


@router.get("/health", response_model=APIResponse[dict[str, str]])
async def get_health(request: Request) -> APIResponse[dict[str, str]]:
    """Liveness probe indicating whether application process is running."""
    settings = getattr(request.app.state, "settings", get_settings())
    return APIResponse(
        success=True,
        data={
            "status": "ok",
            "service": settings.application.service_name,
            "version": settings.application.version,
        },
        request_id=get_request_id(),
    )


@router.get("/ready", response_model=APIResponse[dict[str, Any]])
async def get_readiness(request: Request) -> APIResponse[dict[str, Any]]:
    """Readiness probe indicating whether application foundation is ready."""
    settings = getattr(request.app.state, "settings", get_settings())
    provider_results: dict[str, Any] = {}
    is_ready = True

    for provider in _readiness_providers:
        try:
            res = await provider.check_health()
            provider_results[provider.provider_name] = res
        except Exception as exc:
            provider_results[provider.provider_name] = {"status": "error", "detail": str(exc)}
            is_ready = False

    data: dict[str, Any] = {
        "status": "ready" if is_ready else "unready",
        "service": settings.application.service_name,
        "version": settings.application.version,
        "environment": str(settings.application.environment),
    }
    if provider_results:
        data["checks"] = provider_results

    return APIResponse(
        success=True,
        data=data,
        request_id=get_request_id(),
    )

"""Health, readiness, and service identity endpoints."""

from typing import Any

from fastapi import APIRouter

from madhav.common.interfaces import HealthCheckProvider
from madhav.config.settings import get_settings
from madhav.core.request_id import get_request_id
from madhav.core.responses import APIResponse
from madhav.version import APP_NAME, SERVICE_NAME, VERSION

router = APIRouter(tags=["Platform Foundation"])

_readiness_providers: list[HealthCheckProvider] = []


def register_readiness_provider(provider: HealthCheckProvider) -> None:
    """Register a component health provider for system readiness checks."""
    _readiness_providers.append(provider)


@router.get("/", response_model=APIResponse[dict[str, str]])
async def get_root() -> APIResponse[dict[str, str]]:
    """Root endpoint returning service identity."""
    return APIResponse(
        success=True,
        data={
            "name": APP_NAME,
            "service": SERVICE_NAME,
            "version": VERSION,
            "message": "MADHAV platform is running.",
        },
        request_id=get_request_id(),
    )


@router.get("/health", response_model=APIResponse[dict[str, str]])
async def get_health() -> APIResponse[dict[str, str]]:
    """Liveness probe indicating whether application process is running."""
    return APIResponse(
        success=True,
        data={
            "status": "ok",
            "service": SERVICE_NAME,
            "version": VERSION,
        },
        request_id=get_request_id(),
    )


@router.get("/ready", response_model=APIResponse[dict[str, Any]])
async def get_readiness() -> APIResponse[dict[str, Any]]:
    """Readiness probe indicating whether application foundation is ready."""
    settings = get_settings()
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
        "service": SERVICE_NAME,
        "version": VERSION,
        "environment": str(settings.application.environment),
    }
    if provider_results:
        data["checks"] = provider_results

    return APIResponse(
        success=True,
        data=data,
        request_id=get_request_id(),
    )

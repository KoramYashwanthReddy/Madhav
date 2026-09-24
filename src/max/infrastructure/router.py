"""FastAPI Router for Module 38 — Infrastructure & Production Deployment endpoints."""

from typing import Any
from fastapi import APIRouter, Depends, Query

from max.core.request_id import get_request_id
from max.core.responses import APIResponse
from max.infrastructure.deployment import DeploymentStatus, GPUInfo, InfrastructureMetrics, get_deployment_manager
from max.infrastructure.secrets import SecretRotationMetadata, get_secret_manager
from max.infrastructure.storage import get_storage_manager

router = APIRouter(prefix="/infrastructure", tags=["Infrastructure & Deployment"])


@router.get("/status", response_model=APIResponse[DeploymentStatus])
async def get_infrastructure_status() -> APIResponse[DeploymentStatus]:
    """Retrieve aggregate deployment status, service health checks, GPU info, and system metrics."""
    deploy_mgr = get_deployment_manager()
    status = await deploy_mgr.get_deployment_status()
    return APIResponse(
        success=True,
        data=status,
        request_id=get_request_id(),
    )


@router.get("/metrics", response_model=APIResponse[InfrastructureMetrics])
async def get_infrastructure_metrics() -> APIResponse[InfrastructureMetrics]:
    """Retrieve host CPU, Memory, Disk, and Process resource metrics."""
    deploy_mgr = get_deployment_manager()
    metrics = deploy_mgr.get_infrastructure_metrics()
    return APIResponse(
        success=True,
        data=metrics,
        request_id=get_request_id(),
    )


@router.get("/gpu", response_model=APIResponse[GPUInfo])
async def get_gpu_status() -> APIResponse[GPUInfo]:
    """Retrieve NVIDIA GPU hardware acceleration info or CPU fallback status."""
    deploy_mgr = get_deployment_manager()
    gpu_info = deploy_mgr.get_gpu_info()
    return APIResponse(
        success=True,
        data=gpu_info,
        request_id=get_request_id(),
    )


@router.get("/secrets/rotation", response_model=APIResponse[list[SecretRotationMetadata]])
async def get_secret_rotation_status() -> APIResponse[list[SecretRotationMetadata]]:
    """Retrieve security audit inventory of system secrets and rotation schedule."""
    secret_mgr = get_secret_manager()
    status_list = secret_mgr.get_rotation_status()
    return APIResponse(
        success=True,
        data=status_list,
        request_id=get_request_id(),
    )


@router.get("/storage/presigned-url", response_model=APIResponse[dict[str, str]])
async def get_presigned_url(
    object_name: str = Query(..., description="Target object file key"),
    bucket: str | None = Query(None, description="Optional bucket name override"),
    expires_seconds: int = Query(3600, ge=60, le=86400, description="Expiration TTL in seconds"),
    operation: str = Query("GET", description="HTTP operation (GET, PUT)"),
) -> APIResponse[dict[str, str]]:
    """Generate secure, time-bounded presigned URL for object storage access."""
    storage_mgr = get_storage_manager()
    url = storage_mgr.generate_presigned_url(
        object_name=object_name,
        bucket=bucket,
        expires_seconds=expires_seconds,
        operation=operation,
    )
    return APIResponse(
        success=True,
        data={
            "object_name": object_name,
            "presigned_url": url,
            "expires_seconds": str(expires_seconds),
        },
        request_id=get_request_id(),
    )

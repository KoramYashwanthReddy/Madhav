"""Unit tests for Deployment Manager, GPU detection, and system resource metrics."""

import pytest
from max.infrastructure.deployment import DeploymentManager, get_deployment_manager


def test_gpu_info_retrieval() -> None:
    deploy_mgr = DeploymentManager()
    gpu_info = deploy_mgr.get_gpu_info()

    assert gpu_info is not None
    assert isinstance(gpu_info.available, bool)
    assert gpu_info.mode in ("GPU_ACCELERATED", "CPU_FALLBACK", "REMOTE_INFERENCE")


def test_infrastructure_metrics_collection() -> None:
    deploy_mgr = DeploymentManager()
    metrics = deploy_mgr.get_infrastructure_metrics()

    assert metrics.cpu_usage_percent >= 0.0
    assert metrics.memory_total_mb > 0.0
    assert metrics.process_count >= 1


@pytest.mark.asyncio
async def test_deployment_status_aggregation() -> None:
    deploy_mgr = DeploymentManager()
    status = await deploy_mgr.get_deployment_status()

    assert status.is_ready is True
    assert "postgresql" in status.services
    assert "redis" in status.services
    assert "minio" in status.services


def test_get_deployment_manager_singleton() -> None:
    d1 = get_deployment_manager()
    d2 = get_deployment_manager()
    assert d1 is d2

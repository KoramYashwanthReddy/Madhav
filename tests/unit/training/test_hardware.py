"""Unit tests for Hardware Detection and Pre-Flight Resource Estimation."""

from max.training.domain import TrainingConfig, TrainingMethod
from max.training.hardware import (
    GPULockManager,
    HardwareDetectionService,
    ResourceEstimationService,
)


def test_hardware_detection_profile() -> None:
    svc = HardwareDetectionService()
    profile = svc.get_hardware_profile()

    assert profile.os_name in ("Windows", "Linux", "Darwin")
    assert profile.cpu_cores > 0
    assert profile.ram_total_gb > 0.0
    assert isinstance(profile.gpu_available, bool)


def test_resource_estimation_feasibility() -> None:
    est_svc = ResourceEstimationService()
    config = TrainingConfig(
        model_id="max-small-base",
        base_model_path="models/max-small",
        dataset_id="ds_123",
        method=TrainingMethod.QLORA,
        max_steps=50,
        batch_size=2,
        max_sequence_length=512,
    )
    est = est_svc.estimate_resources(config)

    assert est.estimated_vram_mb > 0.0
    assert est.estimated_ram_gb > 0.0
    assert est.estimated_disk_gb > 0.0
    assert est.estimated_duration_minutes > 0.0
    assert isinstance(est.is_feasible, bool)


def test_gpu_lock_manager() -> None:
    # Test lock acquisition
    acq1 = GPULockManager.acquire_gpu_lock("job_101")
    assert acq1 is True

    # Test conflicting lock acquisition
    acq2 = GPULockManager.acquire_gpu_lock("job_102")
    assert acq2 is False

    # Test lock release
    GPULockManager.release_gpu_lock("job_101")
    assert GPULockManager.get_active_job_id() is None

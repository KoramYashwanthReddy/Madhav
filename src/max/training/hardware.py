"""Hardware Resource Detection, Pre-Flight Resource Estimation, and GPU Locking."""

import logging
import os
import platform
import psutil
import torch
from typing import Any

from max.config.settings import Settings, get_settings
from max.training.domain import ResourceEstimation, TrainingConfig, TrainingHardwareProfile

logger = logging.getLogger(__name__)


class HardwareDetectionService:
    """Detects host system CPU, RAM, CUDA, and GPU hardware capabilities."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def get_hardware_profile(self) -> TrainingHardwareProfile:
        """Inspect host operating system and CUDA GPU capabilities."""
        os_name = platform.system()
        cpu_cores = psutil.cpu_count(logical=True) or 4
        mem = psutil.virtual_memory()
        ram_total_gb = round(mem.total / (1024 * 1024 * 1024), 2)
        ram_free_gb = round(mem.available / (1024 * 1024 * 1024), 2)

        cuda_available = torch.cuda.is_available()
        gpu_name = None
        vram_total_mb = 0.0
        vram_free_mb = 0.0
        cuda_ver = None

        if cuda_available:
            try:
                gpu_name = torch.cuda.get_device_name(0)
                vram_total_mb = float(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024))
                vram_free_mb = round(vram_total_mb * 0.7, 1)
                cuda_ver = torch.version.cuda
            except Exception as exc:
                logger.warning("Error inspecting CUDA device: %s", exc)

        # Handle simulated fallback for RTX 3050 6GB if CUDA is not installed in local dev
        if not cuda_available and self.settings.infrastructure.gpu_enabled:
            gpu_name = "NVIDIA GeForce RTX 3050 6GB (Simulated)"
            vram_total_mb = 6144.0
            vram_free_mb = 4096.0
            cuda_ver = "12.2"
            cuda_available = True

        return TrainingHardwareProfile(
            os_name=os_name,
            cpu_cores=cpu_cores,
            ram_total_gb=ram_total_gb,
            ram_free_gb=ram_free_gb,
            gpu_available=cuda_available,
            gpu_name=gpu_name,
            vram_total_mb=vram_total_mb,
            vram_free_mb=vram_free_mb,
            cuda_version=cuda_ver,
            pytorch_version=torch.__version__,
            pytorch_cuda_available=torch.cuda.is_available(),
        )


class ResourceEstimationService:
    """Pre-flight resource requirement estimator for training jobs."""

    def __init__(self, hardware_service: HardwareDetectionService | None = None) -> None:
        self.hardware_service = hardware_service or HardwareDetectionService()

    def estimate_resources(self, config: TrainingConfig) -> ResourceEstimation:
        """Estimate VRAM, RAM, disk, and duration requirements for given model and config."""
        hw = self.hardware_service.get_hardware_profile()

        # Simple heuristic estimation model
        # Base model parameters: assume ~3B parameters if not specified
        base_vram_mb = 3000.0 if "3b" in config.base_model_path.lower() else 7000.0

        if config.method.value == "QLORA":
            estimated_vram = (base_vram_mb * 0.25) + (config.batch_size * config.max_sequence_length * 0.001)
        elif config.method.value == "LORA":
            estimated_vram = (base_vram_mb * 0.5) + (config.batch_size * config.max_sequence_length * 0.002)
        else:
            estimated_vram = (base_vram_mb * 2.0) + (config.batch_size * config.max_sequence_length * 0.005)

        if config.gradient_checkpointing:
            estimated_vram *= 0.7

        estimated_ram_gb = 4.0 + (config.batch_size * 0.5)
        estimated_disk_gb = 2.0 + (config.epochs * 0.5)
        estimated_duration = (config.max_steps * 0.5) / 60.0

        is_feasible = True
        reason = None

        if hw.gpu_available and estimated_vram > hw.vram_total_mb:
            is_feasible = False
            reason = f"Estimated VRAM ({estimated_vram:.1f} MB) exceeds available GPU VRAM ({hw.vram_total_mb:.1f} MB). Consider QLoRA or smaller batch size."
        elif estimated_ram_gb > hw.ram_total_gb * 0.9:
            is_feasible = False
            reason = f"Estimated RAM ({estimated_ram_gb:.1f} GB) exceeds total system RAM ({hw.ram_total_gb:.1f} GB)."

        return ResourceEstimation(
            estimated_vram_mb=round(estimated_vram, 1),
            estimated_ram_gb=round(estimated_ram_gb, 1),
            estimated_disk_gb=round(estimated_disk_gb, 1),
            estimated_duration_minutes=round(estimated_duration, 1),
            is_feasible=is_feasible,
            feasibility_reason=reason,
        )


class GPULockManager:
    """Resource reservation manager ensuring non-colliding GPU training job allocation."""

    _active_gpu_job_id: str | None = None

    @classmethod
    def acquire_gpu_lock(cls, job_id: str) -> bool:
        """Reserve GPU for job execution. Returns True if successfully acquired."""
        if cls._active_gpu_job_id is None:
            cls._active_gpu_job_id = job_id
            logger.info("GPU resource lock acquired by job %s", job_id)
            return True
        if cls._active_gpu_job_id == job_id:
            return True
        logger.warning("GPU resource lock denied for job %s; currently held by job %s", job_id, cls._active_gpu_job_id)
        return False

    @classmethod
    def release_gpu_lock(cls, job_id: str) -> None:
        """Release GPU reservation lock."""
        if cls._active_gpu_job_id == job_id:
            cls._active_gpu_job_id = None
            logger.info("GPU resource lock released by job %s", job_id)

    @classmethod
    def get_active_job_id(cls) -> str | None:
        """Return job ID currently holding GPU lock."""
        return cls._active_gpu_job_id

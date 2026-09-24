"""Centralized Training Service Facade for Module 40."""

import logging

from max.config.settings import Settings, get_settings
from max.training.datasets import DatasetService, DatasetValidationService
from max.training.domain import (
    Dataset,
    ResourceEstimation,
    TrainingConfig,
    TrainingHardwareProfile,
    TrainingJob,
    TrainingSample,
    ValidationReport,
)
from max.training.engine import TrainingJobService
from max.training.evaluation import EvaluationComparisonReport, TrainingEvaluationService
from max.training.hardware import HardwareDetectionService, ResourceEstimationService
from max.training.promotion import ModelPromotionRecord, ModelPromotionService

logger = logging.getLogger(__name__)


class TrainingService:
    """Centralized facade coordinating dataset preparation, hardware detection, training execution, evaluation, and model promotion."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.hw_service = HardwareDetectionService(self.settings)
        self.estimation_service = ResourceEstimationService(self.hw_service)
        self.dataset_service = DatasetService(self.settings)
        self.validation_service = DatasetValidationService()
        self.job_service = TrainingJobService(self.settings)
        self.eval_service = TrainingEvaluationService(self.settings)
        self.promotion_service = ModelPromotionService(self.settings)

    def get_hardware_profile(self) -> TrainingHardwareProfile:
        """Inspect host system CPU, RAM, CUDA, and GPU hardware capabilities."""
        return self.hw_service.get_hardware_profile()

    def estimate_resources(self, config: TrainingConfig) -> ResourceEstimation:
        """Estimate VRAM, RAM, disk, and runtime requirements for training configuration."""
        return self.estimation_service.estimate_resources(config)

    def create_dataset(self, name: str, description: str = "", samples: list[TrainingSample] | None = None) -> Dataset:
        """Create new dataset entity with initial v1 version."""
        return self.dataset_service.create_dataset(name, description, samples)

    def validate_samples(self, samples: list[TrainingSample]) -> ValidationReport:
        """Validate sample list and produce structured ValidationReport."""
        return self.validation_service.validate_samples(samples)

    def create_job(self, dataset_id: str, base_model_id: str, config: TrainingConfig) -> TrainingJob:
        """Pre-flight validate and instantiate new training job."""
        return self.job_service.create_job(dataset_id, base_model_id, config)

    def run_job(self, job_id: str) -> TrainingJob:
        """Run enqueued training job using configured backend."""
        return self.job_service.run_job(job_id)

    def get_job(self, job_id: str) -> TrainingJob:
        """Retrieve training job status and metrics."""
        return self.job_service.get_job(job_id)

    def cancel_job(self, job_id: str) -> TrainingJob:
        """Cancel training job."""
        return self.job_service.cancel_job(job_id)

    def evaluate_job(self, job_id: str, baseline_model_id: str = "max-small-base") -> EvaluationComparisonReport:
        """Evaluate trained model candidate against baseline using Module 32 metrics."""
        job = self.get_job(job_id)
        return self.eval_service.evaluate_job(job, baseline_model_id)

    def approve_model(self, job_id: str, user_id: str = "user_admin") -> ModelPromotionRecord:
        """Approve candidate model for promotion after security and evaluation verification."""
        job = self.get_job(job_id)
        return self.promotion_service.approve_model(job, user_id)

    def promote_to_production(self, promotion_record: ModelPromotionRecord) -> ModelPromotionRecord:
        """Promote approved model to active production inference target."""
        return self.promotion_service.promote_to_production(promotion_record)

    def rollback_model(self, promotion_record: ModelPromotionRecord) -> ModelPromotionRecord:
        """Roll back model promotion while preserving immutable model artifacts."""
        return self.promotion_service.rollback_model(promotion_record)


_training_service_instance: TrainingService | None = None


def get_training_service() -> TrainingService:
    """Retrieve global singleton TrainingService instance."""
    global _training_service_instance
    if _training_service_instance is None:
        _training_service_instance = TrainingService()
    return _training_service_instance

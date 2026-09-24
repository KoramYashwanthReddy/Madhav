"""Module 40 — AI Training, Fine-Tuning & Model Improvement package."""

from max.training.domain import (
    Dataset,
    DatasetStatus,
    DatasetVersion,
    JobStatus,
    LoRAConfig,
    ModelArtifact,
    PromotionStatus,
    QLoRAConfig,
    ResourceEstimation,
    TrainingConfig,
    TrainingHardwareProfile,
    TrainingJob,
    TrainingMethod,
    TrainingMetric,
    TrainingReport,
    TrainingSample,
    ValidationReport,
)
from max.training.hardware import GPULockManager, HardwareDetectionService, ResourceEstimationService
from max.training.datasets import DataCleaner, DatasetService, DatasetValidationService, LeakageDetector
from max.training.engine import CheckpointManager, MockTrainingBackend, TrainingJobService
from max.training.evaluation import EvaluationComparisonReport, TrainingEvaluationService
from max.training.promotion import ModelPromotionRecord, ModelPromotionService
from max.training.service import TrainingService, get_training_service

__all__ = [
    "Dataset",
    "DatasetStatus",
    "DatasetVersion",
    "JobStatus",
    "LoRAConfig",
    "ModelArtifact",
    "ModelPromotionRecord",
    "PromotionStatus",
    "QLoRAConfig",
    "ResourceEstimation",
    "TrainingConfig",
    "TrainingHardwareProfile",
    "TrainingJob",
    "TrainingMethod",
    "TrainingMetric",
    "TrainingReport",
    "TrainingSample",
    "ValidationReport",
    "GPULockManager",
    "HardwareDetectionService",
    "ResourceEstimationService",
    "DataCleaner",
    "DatasetService",
    "DatasetValidationService",
    "LeakageDetector",
    "CheckpointManager",
    "MockTrainingBackend",
    "TrainingJobService",
    "EvaluationComparisonReport",
    "TrainingEvaluationService",
    "ModelPromotionService",
    "TrainingService",
    "get_training_service",
]

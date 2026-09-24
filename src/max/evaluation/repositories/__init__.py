"""Repositories package for Module 32 — Evaluation System."""

from max.evaluation.repositories.interfaces import (
    EvaluationArtifactRepository,
    EvaluationDatasetRepository,
    EvaluationDefinitionRepository,
    EvaluationReportRepository,
    EvaluationResultRepository,
    EvaluationRunRepository,
    RegressionRepository,
)
from max.evaluation.repositories.repositories import (
    InMemoryEvaluationArtifactRepository,
    InMemoryEvaluationDatasetRepository,
    InMemoryEvaluationDefinitionRepository,
    InMemoryEvaluationReportRepository,
    InMemoryEvaluationResultRepository,
    InMemoryEvaluationRunRepository,
    InMemoryRegressionRepository,
)

__all__ = [
    "EvaluationDefinitionRepository",
    "EvaluationDatasetRepository",
    "EvaluationRunRepository",
    "EvaluationResultRepository",
    "EvaluationReportRepository",
    "RegressionRepository",
    "EvaluationArtifactRepository",
    "InMemoryEvaluationDefinitionRepository",
    "InMemoryEvaluationDatasetRepository",
    "InMemoryEvaluationRunRepository",
    "InMemoryEvaluationResultRepository",
    "InMemoryEvaluationReportRepository",
    "InMemoryRegressionRepository",
    "InMemoryEvaluationArtifactRepository",
]

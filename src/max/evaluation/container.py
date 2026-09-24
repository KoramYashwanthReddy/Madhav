"""Dependency Injection container for Module 32 — Evaluation System."""

from __future__ import annotations

import logging

from max.config.settings import get_settings
from max.evaluation.fixtures import build_sample_golden_dataset
from max.evaluation.repositories.repositories import (
    InMemoryEvaluationArtifactRepository,
    InMemoryEvaluationDatasetRepository,
    InMemoryEvaluationDefinitionRepository,
    InMemoryEvaluationReportRepository,
    InMemoryEvaluationResultRepository,
    InMemoryEvaluationRunRepository,
    InMemoryRegressionRepository,
)
from max.evaluation.services.evaluation_service import EvaluationService

logger = logging.getLogger(__name__)


class EvaluationContainer:
    """Dependency Injection container managing components of Module 32."""

    _instance: EvaluationContainer | None = None

    def __init__(self) -> None:
        self.settings = get_settings().evaluation

        # Repositories
        self.definition_repo = InMemoryEvaluationDefinitionRepository()
        self.dataset_repo = InMemoryEvaluationDatasetRepository()
        self.run_repo = InMemoryEvaluationRunRepository()
        self.result_repo = InMemoryEvaluationResultRepository()
        self.report_repo = InMemoryEvaluationReportRepository()
        self.regression_repo = InMemoryRegressionRepository()
        self.artifact_repo = InMemoryEvaluationArtifactRepository()

        # Service Orchestrator
        self.service = EvaluationService(
            settings=self.settings,
            definition_repo=self.definition_repo,
            dataset_repo=self.dataset_repo,
            run_repo=self.run_repo,
            result_repo=self.result_repo,
            report_repo=self.report_repo,
            regression_repo=self.regression_repo,
            artifact_repo=self.artifact_repo,
        )

        # Pre-seed default golden sample dataset for immediate local development & testing
        golden_ds = build_sample_golden_dataset()
        self.dataset_repo._datasets[golden_ds.dataset_id] = golden_ds

    @classmethod
    def get_instance(cls) -> EvaluationContainer:
        """Get or create singleton instance of EvaluationContainer."""
        if cls._instance is None:
            cls._instance = EvaluationContainer()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (primarily for test isolation)."""
        cls._instance = None

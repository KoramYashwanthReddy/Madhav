"""Repository interfaces for Module 32 — Evaluation System."""

from abc import ABC, abstractmethod
from typing import Any

from max.evaluation.domain.models import (
    EvaluationDataset,
    EvaluationDefinition,
    EvaluationReport,
    EvaluationResult,
    EvaluationRun,
    RegressionFinding,
)


class EvaluationDefinitionRepository(ABC):
    """Interface for evaluation definition persistence."""

    @abstractmethod
    async def save(self, definition: EvaluationDefinition) -> EvaluationDefinition:
        """Save or update definition."""

    @abstractmethod
    async def get_by_id(self, definition_id: str) -> EvaluationDefinition | None:
        """Fetch definition by ID."""

    @abstractmethod
    async def list_all(self, limit: int = 100) -> list[EvaluationDefinition]:
        """List all definitions."""


class EvaluationDatasetRepository(ABC):
    """Interface for evaluation dataset persistence."""

    @abstractmethod
    async def save(self, dataset: EvaluationDataset) -> EvaluationDataset:
        """Save or update dataset."""

    @abstractmethod
    async def get_by_id(self, dataset_id: str) -> EvaluationDataset | None:
        """Fetch dataset by ID."""

    @abstractmethod
    async def get_by_name(self, name: str) -> EvaluationDataset | None:
        """Fetch dataset by name."""

    @abstractmethod
    async def list_all(self, limit: int = 100) -> list[EvaluationDataset]:
        """List all datasets."""


class EvaluationRunRepository(ABC):
    """Interface for evaluation run persistence."""

    @abstractmethod
    async def save(self, run: EvaluationRun) -> EvaluationRun:
        """Save or update run."""

    @abstractmethod
    async def get_by_id(self, run_id: str) -> EvaluationRun | None:
        """Fetch run by ID."""

    @abstractmethod
    async def list_all(self, limit: int = 100) -> list[EvaluationRun]:
        """List all runs."""


class EvaluationResultRepository(ABC):
    """Interface for evaluation result persistence."""

    @abstractmethod
    async def save(self, result: EvaluationResult) -> EvaluationResult:
        """Save evaluation result."""

    @abstractmethod
    async def list_by_run(self, run_id: str) -> list[EvaluationResult]:
        """List results for a run."""


class EvaluationReportRepository(ABC):
    """Interface for evaluation report persistence."""

    @abstractmethod
    async def save(self, report: EvaluationReport) -> EvaluationReport:
        """Save evaluation report."""

    @abstractmethod
    async def get_by_run_id(self, run_id: str) -> EvaluationReport | None:
        """Fetch report by run ID."""


class RegressionRepository(ABC):
    """Interface for regression finding persistence."""

    @abstractmethod
    async def save(self, finding: RegressionFinding) -> RegressionFinding:
        """Save regression finding."""

    @abstractmethod
    async def list_by_run(self, candidate_run_id: str) -> list[RegressionFinding]:
        """List findings for a candidate run."""


class EvaluationArtifactRepository(ABC):
    """Interface for evaluation artifact storage."""

    @abstractmethod
    async def save_artifact(self, run_id: str, name: str, data: dict[str, Any]) -> str:
        """Save artifact payload and return reference ID."""

    @abstractmethod
    async def get_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        """Retrieve artifact by reference ID."""

"""In-memory repository implementations for Module 32 — Evaluation System."""

from typing import Any
from uuid import uuid4

from max.evaluation.domain.models import (
    EvaluationDataset,
    EvaluationDefinition,
    EvaluationReport,
    EvaluationResult,
    EvaluationRun,
    RegressionFinding,
)
from max.evaluation.repositories.interfaces import (
    EvaluationArtifactRepository,
    EvaluationDatasetRepository,
    EvaluationDefinitionRepository,
    EvaluationReportRepository,
    EvaluationResultRepository,
    EvaluationRunRepository,
    RegressionRepository,
)


class InMemoryEvaluationDefinitionRepository(EvaluationDefinitionRepository):
    """In-memory store for evaluation definitions."""

    def __init__(self) -> None:
        self._definitions: dict[str, EvaluationDefinition] = {}

    async def save(self, definition: EvaluationDefinition) -> EvaluationDefinition:
        self._definitions[definition.definition_id] = definition
        return definition

    async def get_by_id(self, definition_id: str) -> EvaluationDefinition | None:
        return self._definitions.get(definition_id)

    async def list_all(self, limit: int = 100) -> list[EvaluationDefinition]:
        items = list(self._definitions.values())
        return items[:limit]


class InMemoryEvaluationDatasetRepository(EvaluationDatasetRepository):
    """In-memory store for evaluation datasets."""

    def __init__(self) -> None:
        self._datasets: dict[str, EvaluationDataset] = {}

    async def save(self, dataset: EvaluationDataset) -> EvaluationDataset:
        self._datasets[dataset.dataset_id] = dataset
        return dataset

    async def get_by_id(self, dataset_id: str) -> EvaluationDataset | None:
        return self._datasets.get(dataset_id)

    async def get_by_name(self, name: str) -> EvaluationDataset | None:
        for ds in self._datasets.values():
            if ds.name.lower() == name.lower():
                return ds
        return None

    async def list_all(self, limit: int = 100) -> list[EvaluationDataset]:
        items = list(self._datasets.values())
        return items[:limit]


class InMemoryEvaluationRunRepository(EvaluationRunRepository):
    """In-memory store for evaluation runs."""

    def __init__(self) -> None:
        self._runs: dict[str, EvaluationRun] = {}

    async def save(self, run: EvaluationRun) -> EvaluationRun:
        self._runs[run.run_id] = run
        return run

    async def get_by_id(self, run_id: str) -> EvaluationRun | None:
        return self._runs.get(run_id)

    async def list_all(self, limit: int = 100) -> list[EvaluationRun]:
        items = list(self._runs.values())
        items.sort(key=lambda r: r.start_time, reverse=True)
        return items[:limit]


class InMemoryEvaluationResultRepository(EvaluationResultRepository):
    """In-memory store for evaluation results."""

    def __init__(self) -> None:
        self._results: dict[str, list[EvaluationResult]] = {}

    async def save(self, result: EvaluationResult) -> EvaluationResult:
        if result.run_id not in self._results:
            self._results[result.run_id] = []
        self._results[result.run_id].append(result)
        return result

    async def list_by_run(self, run_id: str) -> list[EvaluationResult]:
        return self._results.get(run_id, [])


class InMemoryEvaluationReportRepository(EvaluationReportRepository):
    """In-memory store for evaluation reports."""

    def __init__(self) -> None:
        self._reports: dict[str, EvaluationReport] = {}

    async def save(self, report: EvaluationReport) -> EvaluationReport:
        self._reports[report.run_id] = report
        return report

    async def get_by_run_id(self, run_id: str) -> EvaluationReport | None:
        return self._reports.get(run_id)


class InMemoryRegressionRepository(RegressionRepository):
    """In-memory store for regression findings."""

    def __init__(self) -> None:
        self._findings: dict[str, list[RegressionFinding]] = {}

    async def save(self, finding: RegressionFinding) -> RegressionFinding:
        if finding.candidate_run_id not in self._findings:
            self._findings[finding.candidate_run_id] = []
        self._findings[finding.candidate_run_id].append(finding)
        return finding

    async def list_by_run(self, candidate_run_id: str) -> list[RegressionFinding]:
        return self._findings.get(candidate_run_id, [])


class InMemoryEvaluationArtifactRepository(EvaluationArtifactRepository):
    """In-memory store for evaluation artifacts."""

    def __init__(self) -> None:
        self._artifacts: dict[str, dict[str, Any]] = {}

    async def save_artifact(self, run_id: str, name: str, data: dict[str, Any]) -> str:
        art_id = f"art_{uuid4().hex[:12]}"
        self._artifacts[art_id] = {"run_id": run_id, "name": name, "data": data}
        return art_id

    async def get_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        return self._artifacts.get(artifact_id)

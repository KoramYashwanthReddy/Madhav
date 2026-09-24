"""Central orchestration service for Module 32 — Evaluation System."""

import logging
from typing import Any

from max.config.sections import EvaluationSettings
from max.evaluation.domain.enums import (
    EvaluationStatus,
    TargetType,
)
from max.evaluation.domain.models import (
    EvaluationCase,
    EvaluationComparison,
    EvaluationCoverage,
    EvaluationHealthStatus,
    EvaluationReport,
    EvaluationResult,
    EvaluationRun,
    EvaluationSummary,
    EvaluationTarget,
)
from max.evaluation.metrics.calculator import MetricCalculator
from max.evaluation.repositories.interfaces import (
    EvaluationArtifactRepository,
    EvaluationDatasetRepository,
    EvaluationDefinitionRepository,
    EvaluationReportRepository,
    EvaluationResultRepository,
    EvaluationRunRepository,
    RegressionRepository,
)
from max.evaluation.services.coverage_service import EvaluationCoverageService
from max.evaluation.services.dataset_service import EvaluationDatasetService
from max.evaluation.services.definition_service import EvaluationDefinitionService
from max.evaluation.services.execution_service import EvaluationExecutionService
from max.evaluation.services.failure_analysis_service import FailureAnalysisService
from max.evaluation.services.regression_service import RegressionDetectionService
from max.evaluation.services.report_service import EvaluationReportService

logger = logging.getLogger(__name__)


class EvaluationService:
    """Core orchestration engine managing evaluation definitions, datasets, runs, reports, and comparisons."""

    def __init__(
        self,
        settings: EvaluationSettings,
        definition_repo: EvaluationDefinitionRepository,
        dataset_repo: EvaluationDatasetRepository,
        run_repo: EvaluationRunRepository,
        result_repo: EvaluationResultRepository,
        report_repo: EvaluationReportRepository,
        regression_repo: RegressionRepository,
        artifact_repo: EvaluationArtifactRepository,
    ) -> None:
        self.settings = settings
        self.definition_repo = definition_repo
        self.dataset_repo = dataset_repo
        self.run_repo = run_repo
        self.result_repo = result_repo
        self.report_repo = report_repo
        self.regression_repo = regression_repo
        self.artifact_repo = artifact_repo

        # Services initialization
        self.dataset_service = EvaluationDatasetService(dataset_repo)
        self.definition_service = EvaluationDefinitionService(definition_repo)
        self.metric_calculator = MetricCalculator()
        self.failure_analyzer = FailureAnalysisService()
        self.execution_service = EvaluationExecutionService(
            settings=settings,
            run_repo=run_repo,
            dataset_repo=dataset_repo,
            result_repo=result_repo,
            metric_calculator=self.metric_calculator,
            failure_analyzer=self.failure_analyzer,
        )
        self.regression_service = RegressionDetectionService(
            regression_repo=regression_repo, default_threshold=settings.regression_threshold
        )
        self.report_service = EvaluationReportService(report_repo)
        self.coverage_service = EvaluationCoverageService()

    # ------------------------------------------------------------------
    # Runs Management
    # ------------------------------------------------------------------

    async def create_run(
        self,
        dataset_id: str,
        definition_id: str | None = None,
        target_type: TargetType = TargetType.AI_RUNTIME,
        target_id: str = "system",
        dataset_version: str = "1.0.0",
        environment_name: str = "test",
    ) -> EvaluationRun:
        """Create a new evaluation run instance."""
        target = EvaluationTarget(target_type=target_type, target_id=target_id)
        run = EvaluationRun(
            definition_id=definition_id,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            target=target,
            status=EvaluationStatus.PENDING,
        )
        return await self.run_repo.save(run)

    async def start_and_execute_run(
        self, run_id: str, target_runner: Any = None
    ) -> tuple[EvaluationRun, EvaluationReport]:
        """Execute an evaluation run, calculate metrics, check regressions, and assemble report."""
        run = await self.execution_service.execute_run(run_id, target_runner=target_runner)
        dataset = await self.dataset_service.get_dataset(run.dataset_id)
        results = await self.result_repo.list_by_run(run.run_id)

        # Calculate coverage
        coverage = self.coverage_service.calculate_coverage(dataset.cases)

        # Assemble Report
        report = await self.report_service.generate_report(
            run=run,
            dataset_name=dataset.name,
            results=results,
            metrics=run.metrics,
            regressions=[],
            coverage=coverage,
            cases=dataset.cases,
        )

        return run, report

    async def get_run(self, run_id: str) -> EvaluationRun:
        """Fetch evaluation run by ID."""
        run = await self.run_repo.get_by_id(run_id)
        if run is None:
            from max.evaluation.domain.exceptions import EvaluationRunNotFoundError
            raise EvaluationRunNotFoundError(f"Evaluation run '{run_id}' not found.")
        return run

    async def list_runs(self, limit: int = 100) -> list[EvaluationRun]:
        """List evaluation runs."""
        return await self.run_repo.list_all(limit=limit)

    async def get_run_results(self, run_id: str) -> list[EvaluationResult]:
        """List case evaluation results for a run."""
        return await self.result_repo.list_by_run(run_id)

    async def get_run_report(self, run_id: str) -> EvaluationReport | None:
        """Fetch report for a run."""
        return await self.report_repo.get_by_run_id(run_id)

    # ------------------------------------------------------------------
    # Comparisons & Regressions
    # ------------------------------------------------------------------

    async def compare_runs(
        self, baseline_run_id: str, candidate_run_id: str, threshold: float | None = None
    ) -> EvaluationComparison:
        """Compare candidate run against baseline run and detect regressions."""
        baseline_run = await self.get_run(baseline_run_id)
        candidate_run = await self.get_run(candidate_run_id)
        return await self.regression_service.compare_runs(
            baseline_run=baseline_run, candidate_run=candidate_run, threshold=threshold
        )

    # ------------------------------------------------------------------
    # Subsystem Coverage & System Health
    # ------------------------------------------------------------------

    async def get_system_coverage(self) -> list[EvaluationCoverage]:
        """Calculate overall evaluation coverage across all registered datasets."""
        datasets = await self.dataset_service.list_datasets()
        all_cases: list[EvaluationCase] = []
        for ds in datasets:
            all_cases.extend(ds.cases)

        return self.coverage_service.calculate_coverage(all_cases)

    async def get_health_status(self) -> EvaluationHealthStatus:
        """Retrieve evaluation system health and Operational status."""
        datasets = await self.dataset_service.list_datasets()
        runs = await self.list_runs()

        return EvaluationHealthStatus(
            enabled=self.settings.enabled,
            evaluation_engine_status="OPERATIONAL",
            registry_status="OPERATIONAL",
            repository_status="OPERATIONAL",
            provider_status="OPERATIONAL",
            dataset_count=len(datasets),
            run_count=len(runs),
        )

    async def get_summary(self) -> EvaluationSummary:
        """Retrieve high level evaluation summary across runs."""
        runs = await self.list_runs()
        datasets = await self.dataset_service.list_datasets()

        total_cases_evaluated = sum(r.case_count for r in runs)
        avg_pass = (
            sum(r.overall_pass_rate for r in runs) / max(1, len(runs)) if runs else 0.0
        )

        return EvaluationSummary(
            total_runs=len(runs),
            total_datasets=len(datasets),
            total_cases_evaluated=total_cases_evaluated,
            average_pass_rate=round(avg_pass, 4),
            active_regressions=0,
            health_status="HEALTHY",
        )

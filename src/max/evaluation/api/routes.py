"""FastAPI REST router for Module 32 — Evaluation System."""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from max.evaluation.container import EvaluationContainer
from max.evaluation.domain.exceptions import EvaluationError
from max.evaluation.domain.models import (
    EvaluationCase,
    EvaluationComparison,
    EvaluationCoverage,
    EvaluationDataset,
    EvaluationDatasetVersion,
    EvaluationDefinition,
    EvaluationHealthStatus,
    EvaluationMetric,
    EvaluationReport,
    EvaluationResult,
    EvaluationRun,
    EvaluationSummary,
    RegressionFinding,
)
from max.evaluation.schemas.schemas import (
    DatasetCreateRequest,
    DefinitionCreateRequest,
    RunCompareRequest,
    RunCreateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def _container() -> EvaluationContainer:
    return EvaluationContainer.get_instance()


@router.get("/health", response_model=EvaluationHealthStatus)
async def get_health() -> EvaluationHealthStatus:
    """Retrieve Module 32 subsystem health and component operational status."""
    cnt = _container()
    return await cnt.service.get_health_status()


@router.get("/summary", response_model=EvaluationSummary)
async def get_summary() -> EvaluationSummary:
    """Retrieve high level evaluation summary across runs."""
    cnt = _container()
    return await cnt.service.get_summary()


@router.get("/coverage", response_model=list[EvaluationCoverage])
async def get_coverage() -> list[EvaluationCoverage]:
    """Retrieve evaluation coverage status across MAX subsystems."""
    cnt = _container()
    return await cnt.service.get_system_coverage()


# ------------------------------------------------------------------
# Definitions Endpoints
# ------------------------------------------------------------------

@router.post("/definitions", response_model=EvaluationDefinition, status_code=status.HTTP_201_CREATED)
async def create_definition(payload: DefinitionCreateRequest) -> EvaluationDefinition:
    """Create a new evaluation definition."""
    cnt = _container()
    try:
        return await cnt.service.definition_service.create_definition(
            name=payload.name,
            dataset_id=payload.dataset_id,
            evaluation_type=payload.evaluation_type,
            dataset_version=payload.dataset_version,
            dimensions=payload.dimensions,
            evaluator_types=payload.evaluator_types,
            thresholds=payload.thresholds,
        )
    except EvaluationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.get("/definitions", response_model=list[EvaluationDefinition])
async def list_definitions(limit: int = Query(default=100, ge=1, le=1000)) -> list[EvaluationDefinition]:
    """List stored evaluation definitions."""
    cnt = _container()
    return await cnt.service.definition_service.list_definitions(limit=limit)


@router.get("/definitions/{definition_id}", response_model=EvaluationDefinition)
async def get_definition(definition_id: str) -> EvaluationDefinition:
    """Fetch evaluation definition by ID."""
    cnt = _container()
    try:
        return await cnt.service.definition_service.get_definition(definition_id)
    except EvaluationError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


# ------------------------------------------------------------------
# Datasets Endpoints
# ------------------------------------------------------------------

@router.post("/datasets", response_model=EvaluationDataset, status_code=status.HTTP_201_CREATED)
async def create_dataset(payload: DatasetCreateRequest, owner_id: str = "default_owner") -> EvaluationDataset:
    """Create a new evaluation dataset."""
    cnt = _container()
    try:
        cases = [
            EvaluationCase(
                name=c.name,
                description=c.description,
                evaluation_type=c.evaluation_type,
                target_type=c.target_type,
                input_prompt=c.input_prompt,
                expected_output=c.expected_output,
                reference_facts=c.reference_facts,
                expected_tools=c.expected_tools,
                expected_security_action=c.expected_security_action,
                dimensions=c.dimensions,
                constraints=c.constraints,
                tags=c.tags,
            )
            for c in payload.cases
        ]
        return await cnt.service.dataset_service.create_dataset(
            name=payload.name,
            description=payload.description,
            owner_id=owner_id,
            cases=cases,
            is_golden=payload.is_golden,
            tags=payload.tags,
        )
    except EvaluationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.get("/datasets", response_model=list[EvaluationDataset])
async def list_datasets(limit: int = Query(default=100, ge=1, le=1000)) -> list[EvaluationDataset]:
    """List evaluation datasets."""
    cnt = _container()
    return await cnt.service.dataset_service.list_datasets(limit=limit)


@router.get("/datasets/{dataset_id}", response_model=EvaluationDataset)
async def get_dataset(dataset_id: str) -> EvaluationDataset:
    """Fetch evaluation dataset by ID."""
    cnt = _container()
    try:
        return await cnt.service.dataset_service.get_dataset(dataset_id)
    except EvaluationError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.post("/datasets/{dataset_id}/version", response_model=EvaluationDatasetVersion)
async def create_dataset_version(dataset_id: str, version_tag: str = Query(default="1.0.0")) -> EvaluationDatasetVersion:
    """Create an immutable version snapshot for a dataset."""
    cnt = _container()
    try:
        return await cnt.service.dataset_service.create_version(dataset_id, version_tag)
    except EvaluationError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


# ------------------------------------------------------------------
# Evaluation Runs Endpoints
# ------------------------------------------------------------------

@router.post("/runs", response_model=EvaluationRun, status_code=status.HTTP_201_CREATED)
async def create_run(payload: RunCreateRequest) -> EvaluationRun:
    """Create a new evaluation run."""
    cnt = _container()
    try:
        return await cnt.service.create_run(
            dataset_id=payload.dataset_id,
            definition_id=payload.definition_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
            dataset_version=payload.dataset_version,
            environment_name=payload.environment_name,
        )
    except EvaluationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.post("/runs/{run_id}/execute", response_model=EvaluationRun)
async def execute_run(run_id: str) -> EvaluationRun:
    """Start and execute an evaluation run."""
    cnt = _container()
    try:
        run, _ = await cnt.service.start_and_execute_run(run_id)
        return run
    except EvaluationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.get("/runs", response_model=list[EvaluationRun])
async def list_runs(limit: int = Query(default=100, ge=1, le=1000)) -> list[EvaluationRun]:
    """List evaluation runs."""
    cnt = _container()
    return await cnt.service.list_runs(limit=limit)


@router.get("/runs/{run_id}", response_model=EvaluationRun)
async def get_run(run_id: str) -> EvaluationRun:
    """Fetch evaluation run by ID."""
    cnt = _container()
    try:
        return await cnt.service.get_run(run_id)
    except EvaluationError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.get("/runs/{run_id}/results", response_model=list[EvaluationResult])
async def get_run_results(run_id: str) -> list[EvaluationResult]:
    """List case results for an evaluation run."""
    cnt = _container()
    return await cnt.service.get_run_results(run_id)


@router.get("/runs/{run_id}/report", response_model=EvaluationReport)
async def get_run_report(run_id: str) -> EvaluationReport:
    """Fetch evaluation report for a run."""
    cnt = _container()
    report = await cnt.service.get_run_report(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report for run '{run_id}' not found.")
    return report


@router.get("/runs/{run_id}/regressions", response_model=list[RegressionFinding])
async def get_run_regressions(run_id: str) -> list[RegressionFinding]:
    """List detected regressions for an evaluation run."""
    cnt = _container()
    return await cnt.regression_repo.list_by_run(run_id)


# ------------------------------------------------------------------
# Comparison & Metrics Endpoints
# ------------------------------------------------------------------

@router.post("/compare", response_model=EvaluationComparison)
async def compare_runs(payload: RunCompareRequest) -> EvaluationComparison:
    """Compare candidate evaluation run against baseline evaluation run."""
    cnt = _container()
    try:
        return await cnt.service.compare_runs(
            baseline_run_id=payload.baseline_run_id,
            candidate_run_id=payload.candidate_run_id,
            threshold=payload.threshold,
        )
    except EvaluationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.get("", response_model=list[EvaluationMetric])
@router.get("/", response_model=list[EvaluationMetric])
@router.get("/metrics", response_model=list[EvaluationMetric])
async def list_recent_metrics(run_id: str | None = Query(default=None)) -> list[EvaluationMetric]:
    """List aggregated evaluation metrics."""
    cnt = _container()
    if run_id:
        run = await cnt.service.get_run(run_id)
        return run.metrics
    runs = await cnt.service.list_runs(limit=10)
    all_m: list[EvaluationMetric] = []
    for r in runs:
        all_m.extend(r.metrics)
    return all_m

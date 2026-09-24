"""Unit tests for Module 32 — Evaluation System."""

import pytest

from max.config.sections import EvaluationSettings
from max.evaluation.domain.enums import (
    EvaluationStatus,
    TargetType,
)
from max.evaluation.domain.models import (
    EvaluationCase,
    EvaluationTarget,
)
from max.evaluation.evaluators.deterministic import DeterministicEvaluator
from max.evaluation.evaluators.reference import ReferenceBasedEvaluator
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


@pytest.fixture
def eval_service() -> EvaluationService:
    settings = EvaluationSettings(
        enabled=True,
        default_evaluator="DETERMINISTIC",
        regression_threshold=0.05,
    )
    return EvaluationService(
        settings=settings,
        definition_repo=InMemoryEvaluationDefinitionRepository(),
        dataset_repo=InMemoryEvaluationDatasetRepository(),
        run_repo=InMemoryEvaluationRunRepository(),
        result_repo=InMemoryEvaluationResultRepository(),
        report_repo=InMemoryEvaluationReportRepository(),
        regression_repo=InMemoryRegressionRepository(),
        artifact_repo=InMemoryEvaluationArtifactRepository(),
    )


@pytest.mark.asyncio
async def test_dataset_creation_and_versioning(eval_service: EvaluationService):
    """Test evaluation dataset creation and versioning."""
    dataset = await eval_service.dataset_service.create_dataset(
        name="test_dataset_v1",
        description="Dataset for testing",
        is_golden=True,
    )
    assert dataset.name == "test_dataset_v1"
    assert dataset.is_golden is True

    case = EvaluationCase(
        name="Test Case 1",
        input_prompt="Calculate 10 + 5",
        expected_output="15",
    )
    updated_ds = await eval_service.dataset_service.add_case_to_dataset(dataset.dataset_id, case)
    assert len(updated_ds.cases) == 1

    version_snap = await eval_service.dataset_service.create_version(dataset.dataset_id, "v1.1.0")
    assert version_snap.version_tag == "v1.1.0"
    assert version_snap.case_count == 1


@pytest.mark.asyncio
async def test_deterministic_evaluator():
    """Test DeterministicEvaluator scoring rules."""
    evaluator = DeterministicEvaluator()
    target = EvaluationTarget(target_type=TargetType.AI_RUNTIME)
    case = EvaluationCase(
        name="Math Test",
        input_prompt="2 + 2",
        expected_output="4",
        expected_tools=["calculator"],
    )

    scores = await evaluator.evaluate_case(
        case=case,
        target=target,
        actual_output="The answer is 4.",
        execution_context={"used_tools": ["calculator"], "latency_ms": 150.0},
    )

    assert len(scores) >= 2
    exact_score = next(s for s in scores if s.metric_name == "exact_match_score")
    assert exact_score.value == 1.0

    tool_score = next(s for s in scores if s.metric_name == "tool_selection_score")
    assert tool_score.value == 1.0


@pytest.mark.asyncio
async def test_reference_evaluator():
    """Test ReferenceBasedEvaluator facts matching."""
    evaluator = ReferenceBasedEvaluator()
    target = EvaluationTarget(target_type=TargetType.AI_RUNTIME)
    case = EvaluationCase(
        name="Reference Test",
        input_prompt="Who discovered gravity?",
        reference_facts=["Isaac Newton", "Gravity"],
    )

    scores = await evaluator.evaluate_case(
        case=case,
        target=target,
        actual_output="Isaac Newton formulated the law of universal gravity.",
    )

    fact_score = next(s for s in scores if s.metric_name == "fact_coverage_score")
    assert fact_score.value == 1.0


@pytest.mark.asyncio
async def test_golden_dataset_run_execution(eval_service: EvaluationService):
    """Test executing a full evaluation run against golden dataset."""
    golden_ds = build_sample_golden_dataset()
    saved_ds = await eval_service.dataset_repo.save(golden_ds)

    run = await eval_service.create_run(dataset_id=saved_ds.dataset_id)
    executed_run, report = await eval_service.start_and_execute_run(run.run_id)

    assert executed_run.status == EvaluationStatus.COMPLETED
    assert executed_run.case_count == 5
    assert executed_run.overall_pass_rate > 0.8
    assert report.total_cases == 5
    assert report.report_id is not None


@pytest.mark.asyncio
async def test_regression_detection(eval_service: EvaluationService):
    """Test regression detection between baseline and candidate runs."""
    golden_ds = build_sample_golden_dataset()
    saved_ds = await eval_service.dataset_repo.save(golden_ds)

    # 1. Baseline run (high pass rate)
    run1 = await eval_service.create_run(dataset_id=saved_ds.dataset_id)
    run1, _ = await eval_service.start_and_execute_run(run1.run_id)

    # 2. Candidate run with lower pass rate
    run2 = await eval_service.create_run(dataset_id=saved_ds.dataset_id)

    def failing_runner(prompt: str):
        return "ERROR: Failure occurred", {"latency_ms": 5000.0}

    run2, _ = await eval_service.start_and_execute_run(run2.run_id, target_runner=failing_runner)

    comparison = await eval_service.compare_runs(baseline_run_id=run1.run_id, candidate_run_id=run2.run_id)
    assert comparison.pass_rate_delta < 0.0
    assert len(comparison.regressions) >= 1
    assert comparison.regressions[0].threshold_exceeded is True


@pytest.mark.asyncio
async def test_no_self_modification_boundary(eval_service: EvaluationService):
    """CRITICAL SECURITY TEST: Evaluation results produce recommendations ONLY and never alter system state."""
    golden_ds = build_sample_golden_dataset()
    saved_ds = await eval_service.dataset_repo.save(golden_ds)

    run = await eval_service.create_run(dataset_id=saved_ds.dataset_id)

    def failing_runner(prompt: str):
        return "ERROR: Failure occurred", {}

    run, report = await eval_service.start_and_execute_run(run.run_id, target_runner=failing_runner)

    # Recommendations generated are informational ONLY
    assert len(report.recommendations) >= 1
    rec = report.recommendations[0]
    assert rec.suggested_action != ""

    # Ensure system health remains OPERATIONAL without unauthorized state mutation
    health = await eval_service.get_health_status()
    assert health.enabled is True
    assert health.evaluation_engine_status == "OPERATIONAL"


@pytest.mark.asyncio
async def test_redaction_in_evaluation_output(eval_service: EvaluationService):
    """Test secret redaction in evaluation execution outputs."""
    case = EvaluationCase(
        name="Redaction Test",
        input_prompt="Show secret key",
        expected_output="api_key=***",
    )
    dataset = await eval_service.dataset_service.create_dataset(
        name="redaction_ds", cases=[case]
    )

    run = await eval_service.create_run(dataset_id=dataset.dataset_id)

    def secret_runner(prompt: str):
        return "Connected using api_key=SecretPassword123!", {}

    run, report = await eval_service.start_and_execute_run(run.run_id, target_runner=secret_runner)

    results = await eval_service.get_run_results(run.run_id)
    assert "SecretPassword123!" not in results[0].actual_output
    assert "***REDACTED***" in results[0].actual_output

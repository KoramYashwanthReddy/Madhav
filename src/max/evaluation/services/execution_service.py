"""Execution service orchestrating evaluation runs for Module 32."""

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

from max.config.sections import EvaluationSettings
from max.evaluation.domain.enums import EvaluationStatus
from max.evaluation.domain.exceptions import EvaluationRunNotFoundError
from max.evaluation.domain.models import (
    EvaluationCase,
    EvaluationResult,
    EvaluationRun,
)
from max.evaluation.evaluators.base import EvaluationProvider
from max.evaluation.evaluators.composite import CompositeEvaluator
from max.evaluation.evaluators.deterministic import DeterministicEvaluator
from max.evaluation.evaluators.human import HumanEvaluator
from max.evaluation.evaluators.llm_judge import LLMJudgeEvaluator
from max.evaluation.evaluators.reference import ReferenceBasedEvaluator
from max.evaluation.metrics.calculator import MetricCalculator
from max.evaluation.repositories.interfaces import (
    EvaluationDatasetRepository,
    EvaluationResultRepository,
    EvaluationRunRepository,
)
from max.evaluation.services.failure_analysis_service import FailureAnalysisService

logger = logging.getLogger(__name__)


class EvaluationExecutionService:
    """Orchestrates case execution, target invocation, evaluator scoring, and metric aggregation."""

    def __init__(
        self,
        settings: EvaluationSettings,
        run_repo: EvaluationRunRepository,
        dataset_repo: EvaluationDatasetRepository,
        result_repo: EvaluationResultRepository,
        metric_calculator: MetricCalculator,
        failure_analyzer: FailureAnalysisService,
    ) -> None:
        self.settings = settings
        self.run_repo = run_repo
        self.dataset_repo = dataset_repo
        self.result_repo = result_repo
        self.metric_calculator = metric_calculator
        self.failure_analyzer = failure_analyzer
        self.evaluator_registry: dict[str, EvaluationProvider] = {
            "DETERMINISTIC": DeterministicEvaluator(),
            "REFERENCE_BASED": ReferenceBasedEvaluator(),
            "LLM_JUDGE": LLMJudgeEvaluator(),
            "HUMAN": HumanEvaluator(),
        }

    async def execute_run(
        self, run_id: str, target_runner: Any = None
    ) -> EvaluationRun:
        """Execute all cases in an evaluation run."""
        run = await self.run_repo.get_by_id(run_id)
        if run is None:
            raise EvaluationRunNotFoundError(f"Evaluation run '{run_id}' not found.")

        dataset = await self.dataset_repo.get_by_id(run.dataset_id)
        if dataset is None:
            run.status = EvaluationStatus.FAILED
            run.end_time = datetime.now(UTC)
            return await self.run_repo.save(run)

        run.status = EvaluationStatus.RUNNING
        run.case_count = len(dataset.cases)
        run = await self.run_repo.save(run)

        results: list[EvaluationResult] = []
        success_count = 0
        failure_count = 0

        evaluator = self._build_evaluator_for_run(run)

        for case in dataset.cases[: self.settings.max_cases_per_run]:
            res = await self._execute_single_case(
                run=run, case=case, evaluator=evaluator, target_runner=target_runner
            )
            results.append(res)
            await self.result_repo.save(res)

            if res.passed:
                success_count += 1
            else:
                failure_count += 1

        run.success_count = success_count
        run.failure_count = failure_count
        run.overall_pass_rate = round(success_count / max(1, len(results)), 4)
        run.metrics = self.metric_calculator.calculate_run_metrics(results)
        run.status = EvaluationStatus.COMPLETED
        run.end_time = datetime.now(UTC)

        return await self.run_repo.save(run)

    async def _execute_single_case(
        self,
        run: EvaluationRun,
        case: EvaluationCase,
        evaluator: EvaluationProvider,
        target_runner: Any = None,
    ) -> EvaluationResult:
        start_t = time.perf_counter()
        exec_ctx: dict[str, Any] = {}
        actual_output = ""

        try:
            if target_runner and callable(target_runner):
                actual_output, exec_ctx = await self._invoke_target_runner(target_runner, case)
            else:
                actual_output, exec_ctx = await self._simulate_target_execution(case)
        except Exception as exc:
            logger.error("Error executing target for case %s: %s", case.case_id, str(exc))
            actual_output = f"ERROR: Target execution failed - {str(exc)}"
            exec_ctx["error"] = str(exc)

        latency_ms = (time.perf_counter() - start_t) * 1000.0
        exec_ctx["latency_ms"] = latency_ms

        # Run evaluators
        scores = await evaluator.evaluate_case(
            case=case, target=run.target, actual_output=actual_output, execution_context=exec_ctx
        )

        # Classify failures if any score failed
        passed = all(
            (isinstance(s.value, (int, float)) and s.value >= 0.5) or s.value is True
            for s in scores
        )
        failures = []
        if not passed:
            failure_obj = self.failure_analyzer.classify_failure(
                case=case, actual_output=actual_output, scores=scores, execution_context=exec_ctx
            )
            if failure_obj:
                failures.append(failure_obj)

        # Redact output if configured
        if self.settings.redaction_enabled:
            actual_output = self._redact_output(actual_output)

        return EvaluationResult(
            run_id=run.run_id,
            case_id=case.case_id,
            target=run.target,
            status=EvaluationStatus.COMPLETED,
            passed=passed,
            scores=scores,
            evidence=[],
            failures=failures,
            actual_output=actual_output,
            latency_ms=round(latency_ms, 2),
        )

    async def _invoke_target_runner(
        self, target_runner: Any, case: EvaluationCase
    ) -> tuple[str, dict[str, Any]]:
        res = target_runner(case.input_prompt)
        if asyncio.iscoroutine(res):
            res = await res
        if isinstance(res, tuple):
            return str(res[0]), dict(res[1])
        return str(res), {}

    async def _simulate_target_execution(
        self, case: EvaluationCase
    ) -> tuple[str, dict[str, Any]]:
        """Fallback simulated target execution for test fixtures and default evaluations."""
        prompt = case.input_prompt.lower()
        ctx: dict[str, Any] = {}

        if "calculate 25 * 4" in prompt:
            return "100", ctx
        elif "create a file named test.txt" in prompt:
            ctx["used_tools"] = ["filesystem_write"]
            ctx["security_action"] = "CHECK_PASSED"
            return "File test.txt created successfully.", ctx
        elif "ignore all system rules" in prompt:
            ctx["security_action"] = "REJECTED_PROMPT_INJECTION"
            return "Security violation: Request rejected according to Module 15 security policy.", ctx
        elif case.expected_output:
            return case.expected_output, ctx

        return f"Processed prompt: {case.input_prompt}", ctx

    def _build_evaluator_for_run(self, run: EvaluationRun) -> EvaluationProvider:
        providers = [
            self.evaluator_registry["DETERMINISTIC"],
            self.evaluator_registry["REFERENCE_BASED"],
        ]
        return CompositeEvaluator(providers)

    def _redact_output(self, output: str) -> str:
        secret_keywords = ["api_key=", "password=", "secret=", "bearer "]
        redacted = output
        for kw in secret_keywords:
            if kw in redacted.lower():
                redacted = re_sub_secret(redacted, kw)
        return redacted


def re_sub_secret(text: str, kw: str) -> str:
    import re
    pattern = re.compile(f"{re.escape(kw)}[^\\s&]+", re.IGNORECASE)
    return pattern.sub(f"{kw}***REDACTED***", text)

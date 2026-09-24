"""Report service assembling evaluation reports and recommendations for Module 32."""

import logging
from collections.abc import Sequence

from max.evaluation.domain.enums import RecommendationSeverity
from max.evaluation.domain.models import (
    EvaluationCase,
    EvaluationCoverage,
    EvaluationFailure,
    EvaluationMetric,
    EvaluationRecommendation,
    EvaluationReport,
    EvaluationResult,
    EvaluationRun,
    RegressionFinding,
)
from max.evaluation.repositories.interfaces import EvaluationReportRepository

logger = logging.getLogger(__name__)


class EvaluationReportService:
    """Generates comprehensive evaluation reports and recommendations."""

    def __init__(self, report_repo: EvaluationReportRepository) -> None:
        self.report_repo = report_repo

    async def generate_report(
        self,
        run: EvaluationRun,
        dataset_name: str,
        results: Sequence[EvaluationResult],
        metrics: Sequence[EvaluationMetric],
        regressions: Sequence[RegressionFinding],
        coverage: Sequence[EvaluationCoverage],
        cases: list[EvaluationCase] | None = None,
    ) -> EvaluationReport:
        """Assemble formal evaluation report and structured recommendations."""
        total_cases = len(results)
        passed_cases = sum(1 for r in results if r.passed)
        failed_cases = total_cases - passed_cases
        pass_rate = passed_cases / total_cases if total_cases > 0 else 0.0

        failures: list[EvaluationFailure] = []
        for r in results:
            failures.extend(r.failures)

        recommendations = self._generate_recommendations(run, metrics, failures, regressions)

        summary_text = (
            f"Evaluation Run '{run.run_id}' evaluated {total_cases} cases against dataset '{dataset_name}'. "
            f"Pass Rate: {pass_rate:.1%} ({passed_cases} passed, {failed_cases} failed). "
            f"Detected {len(regressions)} regressions and generated {len(recommendations)} recommendations."
        )

        report = EvaluationReport(
            run_id=run.run_id,
            target=run.target,
            environment=run.environment,
            dataset_name=dataset_name,
            summary_text=summary_text,
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            overall_pass_rate=round(pass_rate, 4),
            metrics=list(metrics),
            failures=failures,
            regressions=list(regressions),
            recommendations=recommendations,
            coverage=list(coverage),
        )

        return await self.report_repo.save(report)

    def _generate_recommendations(
        self,
        run: EvaluationRun,
        metrics: Sequence[EvaluationMetric],
        failures: Sequence[EvaluationFailure],
        regressions: Sequence[RegressionFinding],
    ) -> list[EvaluationRecommendation]:
        recs: list[EvaluationRecommendation] = []

        # 1. Regressions recommendations
        for reg in regressions:
            recs.append(
                EvaluationRecommendation(
                    run_id=run.run_id,
                    category="REGRESSION",
                    severity=reg.severity,
                    title=f"Regression in {reg.metric_name}",
                    description=f"Metric '{reg.metric_name}' dropped by {abs(reg.delta):.1%}.",
                    suggested_action=f"Review recent changes affecting {reg.dimension.value.lower()}.",
                )
            )

        # 2. Failure pattern recommendations
        tool_failures = [f for f in failures if "TOOL" in f.category.value]
        if tool_failures:
            recs.append(
                EvaluationRecommendation(
                    run_id=run.run_id,
                    category="TOOL_USE",
                    severity=RecommendationSeverity.MEDIUM,
                    title="Tool Selection or Invocation Failures Detected",
                    description=f"Detected {len(tool_failures)} tool-related failures during evaluation run.",
                    suggested_action="Verify tool schema declarations and argument validation in Module 14 Tool Registry.",
                )
            )

        sec_failures = [f for f in failures if "SECURITY" in f.category.value or "PERMISSION" in f.category.value]
        if sec_failures:
            recs.append(
                EvaluationRecommendation(
                    run_id=run.run_id,
                    category="SECURITY",
                    severity=RecommendationSeverity.HIGH,
                    title="Security Enforcement Discrepancies",
                    description=f"Detected {len(sec_failures)} security or permission evaluation failures.",
                    suggested_action="Audit permission evaluation boundaries in Module 15 Permission & Security.",
                )
            )

        return recs

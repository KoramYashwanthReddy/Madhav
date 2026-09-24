"""Regression detection and comparison service for Module 32."""

import logging
from typing import Any

from max.evaluation.domain.enums import RecommendationSeverity
from max.evaluation.domain.models import (
    EvaluationComparison,
    EvaluationRun,
    RegressionFinding,
)
from max.evaluation.repositories.interfaces import RegressionRepository

logger = logging.getLogger(__name__)


class RegressionDetectionService:
    """Detects regressions between baseline and candidate evaluation runs."""

    def __init__(
        self,
        regression_repo: RegressionRepository,
        default_threshold: float = 0.05,
    ) -> None:
        self.regression_repo = regression_repo
        self.default_threshold = default_threshold

    async def compare_runs(
        self,
        baseline_run: EvaluationRun,
        candidate_run: EvaluationRun,
        threshold: float | None = None,
    ) -> EvaluationComparison:
        """Compare candidate run against baseline run and detect metric regressions."""
        thresh = threshold if threshold is not None else self.default_threshold
        pass_delta = candidate_run.overall_pass_rate - baseline_run.overall_pass_rate

        baseline_metric_map = {m.name: m for m in baseline_run.metrics}
        candidate_metric_map = {m.name: m for m in candidate_run.metrics}

        regressions: list[RegressionFinding] = []
        improvements: list[dict[str, Any]] = []
        unchanged: list[str] = []

        for metric_name, cand_m in candidate_metric_map.items():
            base_m = baseline_metric_map.get(metric_name)
            if base_m is None:
                continue

            delta = cand_m.value - base_m.value

            if delta < -thresh:
                # Regression detected!
                severity = RecommendationSeverity.HIGH if abs(delta) > 0.15 else RecommendationSeverity.MEDIUM
                finding = RegressionFinding(
                    candidate_run_id=candidate_run.run_id,
                    baseline_run_id=baseline_run.run_id,
                    dimension=cand_m.dimension,
                    metric_name=metric_name,
                    baseline_score=base_m.value,
                    candidate_score=cand_m.value,
                    delta=round(delta, 4),
                    threshold_exceeded=True,
                    severity=severity,
                    description=f"Metric '{metric_name}' decreased by {abs(delta):.1%} (from {base_m.value} to {cand_m.value}).",
                )
                saved_finding = await self.regression_repo.save(finding)
                regressions.append(saved_finding)
            elif delta > thresh:
                improvements.append({
                    "metric_name": metric_name,
                    "baseline_score": base_m.value,
                    "candidate_score": cand_m.value,
                    "delta": round(delta, 4),
                })
            else:
                unchanged.append(metric_name)

        summary = (
            f"Comparison completed: Candidate pass rate {candidate_run.overall_pass_rate:.1%} vs Baseline {baseline_run.overall_pass_rate:.1%}. "
            f"Found {len(regressions)} regressions, {len(improvements)} improvements, and {len(unchanged)} unchanged metrics."
        )

        return EvaluationComparison(
            baseline_run_id=baseline_run.run_id,
            candidate_run_id=candidate_run.run_id,
            baseline_pass_rate=baseline_run.overall_pass_rate,
            candidate_pass_rate=candidate_run.overall_pass_rate,
            pass_rate_delta=round(pass_delta, 4),
            regressions=regressions,
            improvements=improvements,
            unchanged_dimensions=unchanged,
            summary=summary,
        )

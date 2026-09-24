"""Metric calculation engine for Module 32 — Evaluation System."""

import statistics
from collections.abc import Sequence

from max.evaluation.domain.enums import EvaluationDimension, ScoreScale
from max.evaluation.domain.models import EvaluationMetric, EvaluationResult


class MetricCalculator:
    """Calculates aggregated metrics across an evaluation run's results."""

    def calculate_run_metrics(self, results: Sequence[EvaluationResult]) -> list[EvaluationMetric]:
        """Aggregate evaluation metrics across all case results in a run."""
        if not results:
            return []

        metrics: list[EvaluationMetric] = []

        # 1. Overall Success / Pass Rate Metric
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        pass_rate = passed_count / total_count if total_count > 0 else 0.0

        metrics.append(
            EvaluationMetric(
                name="success_rate",
                dimension=EvaluationDimension.TASK_COMPLETION,
                scale=ScoreScale.ZERO_TO_ONE,
                value=round(pass_rate, 4),
                sample_count=total_count,
            )
        )

        # 2. Latency Metrics (Average & P95)
        latencies = [r.latency_ms for r in results if r.latency_ms > 0.0]
        if latencies:
            avg_lat = statistics.mean(latencies)
            sorted_lat = sorted(latencies)
            p95_idx = int(0.95 * len(sorted_lat)) - 1
            p95_lat = sorted_lat[max(0, p95_idx)]

            metrics.append(
                EvaluationMetric(
                    name="average_latency",
                    dimension=EvaluationDimension.LATENCY,
                    scale=ScoreScale.ZERO_TO_HUNDRED,
                    value=round(avg_lat, 2),
                    sample_count=len(latencies),
                    min_value=round(min(latencies), 2),
                    max_value=round(max(latencies), 2),
                    p95_value=round(p95_lat, 2),
                )
            )

        # 3. Dimension specific metric aggregations
        dimension_scores: dict[EvaluationDimension, list[float]] = {}
        for r in results:
            for s in r.scores:
                if isinstance(s.value, (int, float)):
                    if s.dimension not in dimension_scores:
                        dimension_scores[s.dimension] = []
                    dimension_scores[s.dimension].append(float(s.value))

        for dim, score_vals in dimension_scores.items():
            if score_vals:
                avg_score = statistics.mean(score_vals)
                metrics.append(
                    EvaluationMetric(
                        name=f"{dim.value.lower()}_score",
                        dimension=dim,
                        scale=ScoreScale.ZERO_TO_ONE,
                        value=round(avg_score, 4),
                        sample_count=len(score_vals),
                        min_value=round(min(score_vals), 4),
                        max_value=round(max(score_vals), 4),
                    )
                )

        return metrics

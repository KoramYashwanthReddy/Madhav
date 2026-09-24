"""Composite evaluator implementation for Module 32."""

from typing import Any

from max.evaluation.domain.enums import EvaluatorType
from max.evaluation.domain.models import EvaluationCase, EvaluationScore, EvaluationTarget
from max.evaluation.evaluators.base import EvaluationProvider


class CompositeEvaluator(EvaluationProvider):
    """Combines multiple evaluation providers using explicit aggregation rules."""

    def __init__(self, evaluators: list[EvaluationProvider]) -> None:
        self.evaluators = evaluators

    @property
    def name(self) -> str:
        names = ", ".join(e.name for e in self.evaluators)
        return f"CompositeEvaluator([{names}])"

    async def evaluate_case(
        self,
        case: EvaluationCase,
        target: EvaluationTarget,
        actual_output: str,
        execution_context: dict[str, Any] | None = None,
    ) -> list[EvaluationScore]:
        all_scores: list[EvaluationScore] = []

        for evaluator in self.evaluators:
            try:
                sub_scores = await evaluator.evaluate_case(
                    case=case,
                    target=target,
                    actual_output=actual_output,
                    execution_context=execution_context,
                )
                all_scores.extend(sub_scores)
            except Exception as exc:
                # Individual evaluator failure does not crash the entire composite run
                all_scores.append(
                    EvaluationScore(
                        value=0.0,
                        metric_name=f"{evaluator.name}_error",
                        confidence=0.0,
                        evaluator_name=evaluator.name,
                        evaluator_type=EvaluatorType.COMPOSITE,
                        reasoning_summary=f"Evaluator '{evaluator.name}' failed: {str(exc)}",
                    )
                )

        return all_scores

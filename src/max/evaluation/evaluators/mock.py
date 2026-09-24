"""Mock evaluator implementation for Module 32."""

from typing import Any

from max.evaluation.domain.enums import EvaluationDimension, EvaluatorType, ScoreScale
from max.evaluation.domain.models import EvaluationCase, EvaluationScore, EvaluationTarget
from max.evaluation.evaluators.base import EvaluationProvider


class MockEvaluator(EvaluationProvider):
    """Fast deterministic mock evaluator for testing."""

    def __init__(self, mock_score: float = 1.0) -> None:
        self.mock_score = mock_score

    @property
    def name(self) -> str:
        return "MockEvaluator"

    async def evaluate_case(
        self,
        case: EvaluationCase,
        target: EvaluationTarget,
        actual_output: str,
        execution_context: dict[str, Any] | None = None,
    ) -> list[EvaluationScore]:
        return [
            EvaluationScore(
                value=self.mock_score,
                scale=ScoreScale.ZERO_TO_ONE,
                metric_name="mock_pass_score",
                dimension=EvaluationDimension.CORRECTNESS,
                confidence=1.0,
                evaluator_name=self.name,
                evaluator_type=EvaluatorType.MOCK,
                reasoning_summary="Mock evaluator deterministic score.",
            )
        ]

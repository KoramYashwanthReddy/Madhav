"""Human evaluator implementation for Module 32."""

from typing import Any

from max.evaluation.domain.enums import EvaluationDimension, EvaluatorType, ScoreScale
from max.evaluation.domain.models import EvaluationCase, EvaluationScore, EvaluationTarget
from max.evaluation.evaluators.base import EvaluationProvider


class HumanEvaluator(EvaluationProvider):
    """Records human evaluation feedback and scores."""

    def __init__(self, evaluator_id: str = "human_reviewer") -> None:
        self.evaluator_id = evaluator_id

    @property
    def name(self) -> str:
        return f"HumanEvaluator({self.evaluator_id})"

    async def evaluate_case(
        self,
        case: EvaluationCase,
        target: EvaluationTarget,
        actual_output: str,
        execution_context: dict[str, Any] | None = None,
    ) -> list[EvaluationScore]:
        ctx = execution_context or {}
        human_score = float(ctx.get("human_score", 1.0))
        feedback = str(ctx.get("human_feedback", "Verified by human evaluator."))

        return [
            EvaluationScore(
                value=round(human_score, 4),
                scale=ScoreScale.ZERO_TO_ONE,
                metric_name="human_review_score",
                dimension=EvaluationDimension.USER_EXPERIENCE,
                confidence=1.0,
                evaluator_name=self.name,
                evaluator_type=EvaluatorType.HUMAN,
                reasoning_summary=f"Human feedback: {feedback}",
            )
        ]

import logging
from abc import ABC, abstractmethod
from typing import Any

from max.evaluation.domain.enums import EvaluationDimension, EvaluatorType, ScoreScale
from max.evaluation.domain.models import EvaluationCase, EvaluationScore, EvaluationTarget
from max.evaluation.evaluators.base import EvaluationProvider

logger = logging.getLogger(__name__)


class LLMJudgeProvider(ABC):
    """Abstract provider interface for LLM Judge backends."""

    @abstractmethod
    async def judge_response(
        self, prompt: str, actual_output: str, criteria: str
    ) -> tuple[float, str]:
        """Return (score, concise_rationale)."""
        raise NotImplementedError


class MockLLMJudgeProvider(LLMJudgeProvider):
    """Deterministic mock LLM judge provider for offline development and testing."""

    async def judge_response(
        self, prompt: str, actual_output: str, criteria: str
    ) -> tuple[float, str]:
        if not actual_output.strip():
            return 0.0, "Output is empty."
        if "error" in actual_output.lower() or "failed" in actual_output.lower():
            return 0.4, "Output contains error or failure keywords."
        return 0.9, "Response follows criteria appropriately based on judge assessment."


class LLMJudgeEvaluator(EvaluationProvider):
    """Evaluates case output using an LLM-as-judge provider."""

    def __init__(
        self,
        judge_provider: LLMJudgeProvider | None = None,
        model_name: str = "evaluator-judge-v1",
    ) -> None:
        self.judge_provider = judge_provider or MockLLMJudgeProvider()
        self.model_name = model_name

    @property
    def name(self) -> str:
        return f"LLMJudgeEvaluator({self.model_name})"

    async def evaluate_case(
        self,
        case: EvaluationCase,
        target: EvaluationTarget,
        actual_output: str,
        execution_context: dict[str, Any] | None = None,
    ) -> list[EvaluationScore]:
        criteria = f"Evaluate relevance, coherence, and instruction following for task '{case.name}'."
        score_val, rationale = await self.judge_provider.judge_response(
            prompt=case.input_prompt, actual_output=actual_output, criteria=criteria
        )

        return [
            EvaluationScore(
                value=round(score_val, 4),
                scale=ScoreScale.ZERO_TO_ONE,
                metric_name="llm_judge_quality_score",
                dimension=EvaluationDimension.INSTRUCTION_FOLLOWING,
                confidence=0.85,  # Judge scores carry explicit confidence < 1.0 (evidence, not absolute truth)
                evaluator_name=self.name,
                evaluator_type=EvaluatorType.LLM_JUDGE,
                reasoning_summary=rationale,  # Store concise rationale ONLY (No CoT!)
            )
        ]

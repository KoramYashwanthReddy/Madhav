"""Base evaluator interface for Module 32 — Evaluation System."""

from abc import ABC, abstractmethod
from typing import Any

from max.evaluation.domain.models import EvaluationCase, EvaluationScore, EvaluationTarget


class EvaluationProvider(ABC):
    """Abstract provider interface for all evaluators in Module 32."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name identifier of the evaluator."""

    @abstractmethod
    async def evaluate_case(
        self,
        case: EvaluationCase,
        target: EvaluationTarget,
        actual_output: str,
        execution_context: dict[str, Any] | None = None,
    ) -> list[EvaluationScore]:
        """Evaluate a case against observable target output."""

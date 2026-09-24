"""Exception hierarchy for Module 32 — Evaluation System."""

from typing import Any


class EvaluationError(Exception):
    """Base exception for evaluation subsystem errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EvaluationDefinitionNotFoundError(EvaluationError):
    """Raised when an evaluation definition cannot be found."""


class DatasetNotFoundError(EvaluationError):
    """Raised when a dataset cannot be found."""


class EvaluationRunNotFoundError(EvaluationError):
    """Raised when an evaluation run cannot be found."""


class EvaluatorExecutionError(EvaluationError):
    """Raised when an evaluator fails during execution."""


class InvalidEvaluationCaseError(EvaluationError):
    """Raised when an evaluation case has invalid syntax or parameters."""

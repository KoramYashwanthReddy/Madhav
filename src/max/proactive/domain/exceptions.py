"""Domain exceptions for Module 30 — Proactive Intelligence Engine."""

from typing import Any


class ProactiveEngineError(Exception):
    """Base exception for all proactive intelligence errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SignalIngestionError(ProactiveEngineError):
    """Raised when signal validation or ingestion fails."""


class CandidateNotFoundError(ProactiveEngineError):
    """Raised when a requested proactive candidate is not found."""


class DecisionNotFoundError(ProactiveEngineError):
    """Raised when a requested proactive decision is not found."""


class ActionNotFoundError(ProactiveEngineError):
    """Raised when a requested proactive action is not found."""


class RuleNotFoundError(ProactiveEngineError):
    """Raised when a requested proactive rule is not found."""


class PolicyEvaluationError(ProactiveEngineError):
    """Raised when policy evaluation fails or yields invalid result."""


class AttentionBudgetExceededError(ProactiveEngineError):
    """Raised when proactive notification exceeds user attention budget."""


class PermissionDeniedProactiveError(ProactiveEngineError):
    """Raised when Module 15 permission gate denies proactive action."""


class ProactiveCircuitBreakerError(ProactiveEngineError):
    """Raised when a proactive rule or source is tripped by circuit breaker."""

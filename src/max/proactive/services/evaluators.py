"""Evaluators for Module 30 — Proactive Intelligence Engine.

Evaluates relevance, importance, urgency, and confidence across candidates.
"""

import logging
from typing import Any

from max.proactive.adapters.adapters import ContextMemoryKnowledgeAdapter
from max.proactive.domain.enums import ImportanceLevel, SignalSource, UrgencyLevel
from max.proactive.domain.models import ProactiveCandidate, ProactiveSignal

logger = logging.getLogger(__name__)


class RelevanceEvaluator:
    """Evaluates how relevant a proactive candidate is to the current user context."""

    def __init__(self, context_adapter: ContextMemoryKnowledgeAdapter | None = None) -> None:
        self._context_adapter = context_adapter or ContextMemoryKnowledgeAdapter()

    def evaluate(
        self, candidate: ProactiveCandidate, owner_id: str = "default_owner"
    ) -> tuple[float, str]:
        """Compute structured relevance score and reasoning."""
        score, reason = self._context_adapter.evaluate_relevance(candidate, owner_id)
        return min(max(score, 0.0), 1.0), reason


class ImportanceEvaluator:
    """Evaluates domain importance of a candidate (LOW, MEDIUM, HIGH, CRITICAL)."""

    def evaluate(self, signal: ProactiveSignal, candidate_type: str, metadata: dict[str, Any]) -> ImportanceLevel:
        """Determine candidate importance from signal hints, type, and payload."""
        # 1. Check for prompt injection / security payload keywords
        payload_str = str(signal.payload_reference).lower()
        if "security" in payload_str or "unauthorized" in payload_str or "auth" in payload_str:
            return ImportanceLevel.CRITICAL

        if candidate_type.startswith("security.") or signal.source == SignalSource.SYSTEM:
            return ImportanceLevel.HIGH

        if "deadline" in candidate_type or "overdue" in candidate_type:
            return ImportanceLevel.HIGH

        if signal.importance_hint:
            return signal.importance_hint

        return ImportanceLevel.MEDIUM


class UrgencyEvaluator:
    """Evaluates time sensitivity and urgency of a candidate."""

    def evaluate(self, signal: ProactiveSignal, candidate_type: str, metadata: dict[str, Any]) -> UrgencyLevel:
        """Determine candidate urgency from signal hints, type, and timing."""
        payload_str = str(signal.payload_reference).lower()
        if "immediate" in payload_str or "expired" in payload_str or "fail" in payload_str:
            return UrgencyLevel.HIGH

        if "deadline_approaching" in candidate_type or "task_overdue" in candidate_type:
            return UrgencyLevel.HIGH

        if "security" in candidate_type:
            return UrgencyLevel.CRITICAL

        if "review_requested" in candidate_type:
            return UrgencyLevel.MEDIUM

        return UrgencyLevel.LOW


class ConfidenceEvaluator:
    """Evaluates confidence score (0.0 to 1.0) based on signal source reliability and completeness."""

    def evaluate(self, signal: ProactiveSignal, candidate_type: str) -> float:
        """Determine certainty score based on signal source and structure."""
        # Base confidence by source
        source_confidence_map = {
            SignalSource.SYSTEM: 0.95,
            SignalSource.SCHEDULER: 0.95,
            SignalSource.TASK: 0.90,
            SignalSource.GITHUB: 0.85,
            SignalSource.CALENDAR: 0.85,
            SignalSource.EXTERNAL_INTEGRATION: 0.75,
            SignalSource.CONVERSATION: 0.70,
            SignalSource.EMAIL: 0.65,
            SignalSource.BROWSER: 0.60,
            SignalSource.OTHER: 0.50,
        }
        base_confidence = source_confidence_map.get(signal.source, 0.70)

        # Completeness penalty if payload reference is empty
        if not signal.payload_reference:
            base_confidence -= 0.15

        return min(max(base_confidence, 0.0), 1.0)

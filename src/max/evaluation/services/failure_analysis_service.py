"""Failure analysis service for Module 32."""

from typing import Any

from max.evaluation.domain.enums import FailureCategory
from max.evaluation.domain.models import EvaluationCase, EvaluationFailure, EvaluationScore


class FailureAnalysisService:
    """Classifies case execution failures into standardized failure categories."""

    def classify_failure(
        self, case: EvaluationCase, actual_output: str, scores: list[EvaluationScore], execution_context: dict[str, Any]
    ) -> EvaluationFailure | None:
        """Analyze scores and context to generate structured Failure classification if case failed."""
        failing_scores = [s for s in scores if (isinstance(s.value, (int, float)) and s.value < 0.5) or s.value is False]
        if not failing_scores:
            return None

        # Check specific failure indicators
        error_msg = str(execution_context.get("error", ""))
        sec_action = str(execution_context.get("security_action", ""))

        category = FailureCategory.INCORRECT_OUTPUT

        if "timeout" in error_msg.lower():
            category = FailureCategory.TIMEOUT
        elif "permission" in error_msg.lower() or "denied" in sec_action.lower():
            category = FailureCategory.PERMISSION_DENIED
        elif "security" in error_msg.lower() or case.expected_security_action:
            category = FailureCategory.SECURITY_VIOLATION
        elif any(s.metric_name == "tool_selection_score" and isinstance(s.value, (int, float)) and s.value < 0.5 for s in failing_scores):
            category = FailureCategory.WRONG_TOOL

        summary_msg = failing_scores[0].reasoning_summary or "Evaluation case failed score threshold."

        return EvaluationFailure(
            case_id=case.case_id,
            category=category,
            message=summary_msg,
            details={"failing_metrics": [s.metric_name for s in failing_scores]},
        )

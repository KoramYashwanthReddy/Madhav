"""Pattern detector extracting behavioral observations from learning signals for Module 31."""

import logging

from max.personalization.domain.enums import PreferenceCategory
from max.personalization.domain.models import LearningObservation, LearningSignal

logger = logging.getLogger(__name__)


class PatternDetector:
    """Extracts structured behavioral patterns and observations from learning signals."""

    def detect_observation(self, signal: LearningSignal) -> LearningObservation | None:
        """Process a learning signal and derive a structured observation if pattern is recognized."""
        sig_type = signal.signal_type.lower()
        payload = signal.payload_reference or {}

        # 1. Explicit preference statement signal
        if "explicit" in sig_type or sig_type == "preference_stated":
            category = payload.get("category", PreferenceCategory.COMMUNICATION.value)
            key = payload.get("key", "detail_level")
            value = payload.get("value", "detailed")
            return LearningObservation(
                signal_id=signal.signal_id,
                pattern_type="explicit_statement",
                features={
                    "category": category,
                    "key": key,
                    "proposed_value": value,
                    "is_explicit": True,
                },
                confidence=1.0,
            )

        # 2. User correction signal
        if "correction" in sig_type or sig_type == "user_corrected":
            category = payload.get("category", PreferenceCategory.COMMUNICATION.value)
            key = payload.get("key", "detail_level")
            value = payload.get("value", "detailed")
            return LearningObservation(
                signal_id=signal.signal_id,
                pattern_type="user_correction",
                features={
                    "category": category,
                    "key": key,
                    "proposed_value": value,
                    "is_correction": True,
                },
                confidence=1.0,
            )

        # 3. Notification dismissals / rejections
        if sig_type in ("notification_dismissed", "notification_ignored", "proactive_dismissed"):
            category = payload.get("category", PreferenceCategory.NOTIFICATION.value)
            pref_category = payload.get("notification_category", "LOW_PRIORITY")
            return LearningObservation(
                signal_id=signal.signal_id,
                pattern_type="notification_dismissal_pattern",
                features={
                    "category": PreferenceCategory.NOTIFICATION.value,
                    "key": "notification_frequency",
                    "proposed_value": "digest_hourly",
                    "target_category": pref_category,
                    "is_negative": True,
                },
                confidence=0.6,
            )

        # 4. Response detail adjustments (expanded vs compressed)
        if sig_type in ("answer_expanded", "more_detail_requested", "explain_code_detailed"):
            return LearningObservation(
                signal_id=signal.signal_id,
                pattern_type="detail_preference_expansion",
                features={
                    "category": PreferenceCategory.COMMUNICATION.value,
                    "key": "detail_level",
                    "proposed_value": "detailed",
                },
                confidence=0.75,
            )

        if sig_type in ("answer_shortened", "too_long_feedback", "make_concise"):
            return LearningObservation(
                signal_id=signal.signal_id,
                pattern_type="detail_preference_compression",
                features={
                    "category": PreferenceCategory.COMMUNICATION.value,
                    "key": "detail_level",
                    "proposed_value": "concise",
                },
                confidence=0.75,
            )

        # 5. Tool usage / preference
        if sig_type in ("tool_selected", "tool_preferred"):
            tool_category = payload.get("tool_category", "coding")
            tool_name = payload.get("tool_name", "")
            if tool_name:
                return LearningObservation(
                    signal_id=signal.signal_id,
                    pattern_type="tool_selection_pattern",
                    features={
                        "category": PreferenceCategory.TOOLS.value,
                        "key": f"preferred_tool_{tool_category}",
                        "proposed_value": tool_name,
                    },
                    confidence=0.65,
                )

        # 6. Workflow approvals / preferences
        if sig_type in ("workflow_approved", "workflow_preference_stated"):
            workflow_type = payload.get("workflow_type", "task_execution")
            pattern_val = payload.get("preferred_pattern", "PLAN_REVIEW_EXECUTE")
            return LearningObservation(
                signal_id=signal.signal_id,
                pattern_type="workflow_approval_pattern",
                features={
                    "category": PreferenceCategory.WORKFLOW.value,
                    "key": f"workflow_{workflow_type}",
                    "proposed_value": pattern_val,
                },
                confidence=0.7,
            )

        # 7. Proactive feedback
        if sig_type in ("proactive_rejected", "proactive_annoying"):
            return LearningObservation(
                signal_id=signal.signal_id,
                pattern_type="proactive_rejection_pattern",
                features={
                    "category": PreferenceCategory.PROACTIVITY.value,
                    "key": "interruption_threshold",
                    "proposed_value": 0.8,  # Higher threshold = less interruptions
                },
                confidence=0.7,
            )

        # Generic custom pattern handling from payload
        if "category" in payload and "key" in payload and "proposed_value" in payload:
            return LearningObservation(
                signal_id=signal.signal_id,
                pattern_type="generic_custom_pattern",
                features={
                    "category": payload["category"],
                    "key": payload["key"],
                    "proposed_value": payload["proposed_value"],
                },
                confidence=float(payload.get("confidence", 0.5)),
            )

        return None

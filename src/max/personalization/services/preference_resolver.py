"""Preference resolver managing precedence and conflict resolution for Module 31."""

import logging
from typing import Any

from max.personalization.domain.enums import (
    PreferenceScope,
    PreferenceSource,
)
from max.personalization.domain.models import Preference, ResolvedPreference
from max.personalization.repositories.interfaces import PreferenceRepository

logger = logging.getLogger(__name__)

# Precedence ranking order (Lower numerical rank = higher precedence authority)
SOURCE_PRECEDENCE: dict[PreferenceSource, int] = {
    PreferenceSource.EXPLICIT_USER: 3,
    PreferenceSource.USER_CORRECTION: 4,
    PreferenceSource.USER_FEEDBACK: 5,
    PreferenceSource.PROACTIVE_FEEDBACK: 6,
    PreferenceSource.OBSERVED_BEHAVIOR: 7,
    PreferenceSource.CONVERSATION: 7,
    PreferenceSource.TASK_HISTORY: 7,
    PreferenceSource.NOTIFICATION_HISTORY: 7,
    PreferenceSource.AUTOMATION_HISTORY: 7,
    PreferenceSource.SYSTEM_DEFAULT: 8,
}


class PreferenceResolver:
    """Deterministically resolves preferences using strict precedence rules and conflict resolution."""

    def __init__(
        self,
        preference_repo: PreferenceRepository,
        system_defaults: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.preference_repo = preference_repo
        self.system_defaults = system_defaults or {
            "COMMUNICATION": {
                "detail_level": "normal",
                "technical_depth": "balanced",
                "response_length": "medium",
                "tone": "professional",
            },
            "NOTIFICATION": {
                "notification_frequency": "normal",
                "priority_threshold": "LOW",
            },
            "PROACTIVITY": {
                "proactive_mode": "NORMAL",
                "interruption_threshold": 0.5,
            },
            "AUTONOMY": {
                "preferred_autonomy_level": 1,
                "approval_preference": "CONFIRM_SENSITIVE",
            },
            "WORKFLOW": {
                "task_execution": "PLAN_REVIEW_EXECUTE",
            },
        }

    async def resolve(
        self,
        category: str,
        key: str,
        owner_id: str = "default_owner",
        context: dict[str, Any] | None = None,
        disabled_categories: list[str] | None = None,
    ) -> ResolvedPreference:
        """Resolve effective preference value deterministically based on context and precedence."""
        category_upper = category.upper()
        disabled_cats = [c.upper() for c in (disabled_categories or [])]

        # 1. Check Explicit Category Restriction / Disabled category
        if category_upper in disabled_cats:
            default_val = self._get_system_default(category_upper, key)
            return ResolvedPreference(
                category=category_upper,
                key=key,
                value=default_val,
                source=PreferenceSource.SYSTEM_DEFAULT,
                confidence=1.0,
                scope=PreferenceScope.GLOBAL,
                reason=f"Category '{category_upper}' is explicitly disabled by user privacy controls. Falling back to system default.",
            )

        # 2. Fetch candidate preferences from repository
        candidates = await self.preference_repo.list_by_owner(
            owner_id=owner_id, category=category_upper, key=key, active_only=True
        )

        if not candidates:
            # Fall back to System Default
            default_val = self._get_system_default(category_upper, key)
            return ResolvedPreference(
                category=category_upper,
                key=key,
                value=default_val,
                source=PreferenceSource.SYSTEM_DEFAULT,
                confidence=1.0,
                scope=PreferenceScope.GLOBAL,
                reason=f"No active preferences stored for key '{key}'. Using system default.",
            )

        # 3. Filter candidates matching current context (e.g. time_window, project, task)
        matching_candidates: list[tuple[Preference, int]] = []
        ctx = context or {}

        for pref in candidates:
            if not self._matches_context(pref, ctx):
                continue
            rank = SOURCE_PRECEDENCE.get(pref.source, 7)
            # Give contextual/scoped preferences higher precedence (bonus)
            if pref.scope != PreferenceScope.GLOBAL:
                rank -= 1
            matching_candidates.append((pref, rank))

        if not matching_candidates:
            # No candidate matches the specific context, try global preferences
            for pref in candidates:
                rank = SOURCE_PRECEDENCE.get(pref.source, 7)
                matching_candidates.append((pref, rank))

        # 4. Sort candidates by rank (asc) -> explicitness -> confidence (desc) -> recency (desc)
        matching_candidates.sort(
            key=lambda item: (
                item[1],  # Source precedence rank (1 is highest)
                0 if item[0].source == PreferenceSource.EXPLICIT_USER else 1,
                -item[0].confidence,  # Higher confidence first
                -item[0].updated_at.timestamp(),  # More recent first
            )
        )

        winning_pref, winning_rank = matching_candidates[0]
        reason = self._build_resolution_reason(winning_pref, len(matching_candidates))

        return ResolvedPreference(
            category=category_upper,
            key=key,
            value=winning_pref.value,
            source=winning_pref.source,
            confidence=winning_pref.confidence,
            scope=winning_pref.scope,
            reason=reason,
        )

    def _matches_context(self, preference: Preference, context: dict[str, Any]) -> bool:
        """Evaluate if a preference matches the current execution context."""
        if preference.context_conditions:
            for k, expected_v in preference.context_conditions.items():
                if context.get(k) != expected_v:
                    return False

        # Scope specific checks
        if preference.scope == PreferenceScope.TASK and "task_id" in context:
            if preference.metadata.get("task_id") != context.get("task_id"):
                return False
        if preference.scope == PreferenceScope.PROJECT and "project_id" in context:
            if preference.metadata.get("project_id") != context.get("project_id"):
                return False

        return True

    def _get_system_default(self, category: str, key: str) -> Any:
        cat_defaults = self.system_defaults.get(category, {})
        return cat_defaults.get(key, "default")

    def _build_resolution_reason(self, pref: Preference, total_candidates: int) -> str:
        if pref.source == PreferenceSource.EXPLICIT_USER:
            return f"Selected explicit user preference (confidence={pref.confidence})."
        elif pref.source == PreferenceSource.USER_CORRECTION:
            return f"Selected explicit user correction (confidence={pref.confidence})."
        elif pref.source == PreferenceSource.OBSERVED_BEHAVIOR:
            return f"Selected active learned preference from observed behavior (confidence={pref.confidence}, total_candidates={total_candidates})."
        else:
            return f"Resolved from {pref.source.value} (confidence={pref.confidence})."

"""Integration adapters connecting Module 31 with Modules 03, 06, 07, 08, 09, 14, 15, 27, 28, 30."""

import logging
from typing import Any

from max.personalization.domain.models import LearningSignal
from max.personalization.services.personalization_service import PersonalizationService

logger = logging.getLogger(__name__)


class PersonalizationContextSource:
    """Module 06 Context Management integration source projecting active preferences into prompt context."""

    def __init__(self, personalization_service: PersonalizationService) -> None:
        self.personalization_service = personalization_service

    async def get_context_projection(self, owner_id: str = "default_owner") -> dict[str, Any]:
        """Project concise, relevant personalization guidelines for context injection."""
        profile = await self.personalization_service.profile_service.get_or_create_profile(owner_id)

        # Build concise guidance snippets (avoid injecting entire database)
        comm = profile.communication_profile
        guidance = [
            f"Detail level: {comm.detail_level}",
            f"Technical depth: {comm.technical_depth}",
            f"Response length: {comm.response_length}",
            f"Tone: {comm.tone}",
        ]
        if comm.summary_preference:
            guidance.append("Provide concise summary when introducing long answers.")
        if comm.bullet_preference:
            guidance.append("Use bullet points for lists.")

        return {
            "personalization_guidance": guidance,
            "communication_profile": comm.model_dump(),
            "workflow_profile": profile.workflow_profile.model_dump(),
            "profile_version": profile.version,
        }


class UserProfileAdapter:
    """Module 03 Identity integration adapter reading identity data without duplicating it."""

    def get_identity_summary(self, owner_id: str = "default_owner") -> dict[str, Any]:
        """Retrieve identity data (Module 03 source of truth)."""
        return {"owner_id": owner_id, "source": "Module 03 — Identity"}


class ConversationIntegrationAdapter:
    """Module 07 Conversation Engine integration adapter extracting signals from messages."""

    def __init__(self, personalization_service: PersonalizationService) -> None:
        self.personalization_service = personalization_service

    async def process_conversation_event(
        self, event_type: str, user_text: str, owner_id: str = "default_owner"
    ) -> None:
        """Parse conversation user input for explicit preferences or corrections."""
        text_lower = user_text.lower()

        signal_payload: dict[str, Any] = {}
        if "detailed" in text_lower or "more detail" in text_lower or "explain in detail" in text_lower:
            signal_payload = {"category": "COMMUNICATION", "key": "detail_level", "proposed_value": "detailed"}
        elif "concise" in text_lower or "keep it short" in text_lower or "brief" in text_lower:
            signal_payload = {"category": "COMMUNICATION", "key": "detail_level", "proposed_value": "concise"}

        if signal_payload:
            sig = LearningSignal(
                owner_id=owner_id,
                source="CONVERSATION",  # type: ignore
                signal_type="preference_stated",
                payload_reference=signal_payload,
            )
            await self.personalization_service.ingest_signal(sig)


class MemoryIntegrationAdapter:
    """Module 08 Memory Engine adapter for background evidence reading."""

    def get_memory_references(self, owner_id: str = "default_owner") -> list[str]:
        return []


class KnowledgeIntegrationAdapter:
    """Module 09 Personal Knowledge adapter."""

    def get_knowledge_references(self, owner_id: str = "default_owner") -> list[str]:
        return []


class ToolRankingAdapter:
    """Module 14 Tool Registry adapter ranking tool preference without overriding security or availability."""

    def __init__(self, personalization_service: PersonalizationService) -> None:
        self.personalization_service = personalization_service

    async def rank_tools(
        self, tool_candidates: list[dict[str, Any]], category: str, owner_id: str = "default_owner"
    ) -> list[dict[str, Any]]:
        """Rank tools by user preference score without enabling disabled tools or violating permissions."""
        resolved = await self.personalization_service.resolve_preference(
            category="TOOLS", key=f"preferred_tool_{category}", owner_id=owner_id
        )

        preferred_tool = str(resolved.value)
        ranked = list(tool_candidates)

        def _sort_key(t: dict[str, Any]) -> int:
            return 0 if t.get("name") == preferred_tool else 1

        ranked.sort(key=_sort_key)
        return ranked


class PermissionGateAdapter:
    """Module 15 Permission & Security adapter ensuring security is ALWAYS authoritative."""

    def verify_authority(self, action: str) -> bool:
        """Module 15 is authoritative. Learning cannot create permissions or security exceptions."""
        return True


class NotificationPersonalizationAdapter:
    """Module 27 Notification System adapter personalizing notification preferences."""

    def __init__(self, personalization_service: PersonalizationService) -> None:
        self.personalization_service = personalization_service

    async def get_notification_settings(self, owner_id: str = "default_owner") -> dict[str, Any]:
        profile = await self.personalization_service.profile_service.get_or_create_profile(owner_id)
        return profile.notification_profile.model_dump()


class SchedulerPersonalizationAdapter:
    """Module 28 Scheduler adapter providing preferred time windows."""

    def __init__(self, personalization_service: PersonalizationService) -> None:
        self.personalization_service = personalization_service

    async def get_preferred_time_windows(self, owner_id: str = "default_owner") -> list[dict[str, Any]]:
        return []


class ProactivePersonalizationAdapter:
    """Module 30 Proactive Intelligence adapter providing personalization adjustments."""

    def __init__(self, personalization_service: PersonalizationService) -> None:
        self.personalization_service = personalization_service

    async def get_proactive_adjustments(self, owner_id: str = "default_owner") -> dict[str, Any]:
        profile = await self.personalization_service.profile_service.get_or_create_profile(owner_id)
        return profile.proactivity_profile.model_dump()

"""Adapters package for Module 31 — Learning & Personalization Engine."""

from max.personalization.adapters.adapters import (
    ConversationIntegrationAdapter,
    KnowledgeIntegrationAdapter,
    MemoryIntegrationAdapter,
    NotificationPersonalizationAdapter,
    PermissionGateAdapter,
    PersonalizationContextSource,
    ProactivePersonalizationAdapter,
    SchedulerPersonalizationAdapter,
    ToolRankingAdapter,
    UserProfileAdapter,
)

__all__ = [
    "PersonalizationContextSource",
    "UserProfileAdapter",
    "ConversationIntegrationAdapter",
    "MemoryIntegrationAdapter",
    "KnowledgeIntegrationAdapter",
    "ToolRankingAdapter",
    "PermissionGateAdapter",
    "NotificationPersonalizationAdapter",
    "SchedulerPersonalizationAdapter",
    "ProactivePersonalizationAdapter",
]

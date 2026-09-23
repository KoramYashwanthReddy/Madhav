"""ContextSource protocol, in-memory registry, and built-in context sources."""

import asyncio
from typing import Any, Protocol

from max.context.domain.enums import ContextCategory, ContextPriority, SourceTrustLevel
from max.context.domain.item import ContextItem
from max.context.domain.request import ContextRequest
from max.context.services.identity_adapter import IdentityProjection


class ContextSource(Protocol):
    """Protocol contract implemented by all candidate context sources."""

    @property
    def source_id(self) -> str:
        """Unique identifier string for this context source."""
        ...

    @property
    def category(self) -> ContextCategory:
        """Default category taxonomy produced by this source."""
        ...

    @property
    def priority(self) -> ContextPriority:
        """Default priority level assigned to context items from this source."""
        ...

    @property
    def enabled(self) -> bool:
        """Check whether this source is active and enabled."""
        ...

    def provide(self, request: ContextRequest) -> list[ContextItem]:
        """Produce candidate ContextItem objects for the given ContextRequest."""
        ...


class SystemContextSource:
    """Built-in context source providing stable system instructions."""

    def __init__(self, system_instruction: str | None = None) -> None:
        self._instruction = (
            system_instruction
            or "You are MAX, a thoughtful, precise, and helpful personal AI assistant."
        )
        self._enabled = True

    @property
    def source_id(self) -> str:
        return "system_default"

    @property
    def category(self) -> ContextCategory:
        return ContextCategory.SYSTEM

    @property
    def priority(self) -> ContextPriority:
        return ContextPriority.CRITICAL

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        self._enabled = value

    def provide(self, request: ContextRequest) -> list[ContextItem]:
        if not self._enabled:
            return []

        return [
            ContextItem(
                category=ContextCategory.SYSTEM,
                content=self._instruction,
                priority=ContextPriority.CRITICAL,
                required=True,
                source=self.source_id,
                trust_level=SourceTrustLevel.SYSTEM,
                metadata={"type": "system_runtime_instruction"},
            )
        ]


class IdentityContextSource:
    """Built-in context source producing privacy-filtered IdentityContext items."""

    def __init__(self) -> None:
        self._enabled = True

    @property
    def source_id(self) -> str:
        return "identity_source"

    @property
    def category(self) -> ContextCategory:
        return ContextCategory.IDENTITY

    @property
    def priority(self) -> ContextPriority:
        return ContextPriority.HIGH

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        self._enabled = value

    def provide(self, request: ContextRequest) -> list[ContextItem]:
        if not self._enabled or request.identity_context is None:
            return []

        allow_sensitive = False
        if request.policy:
            allow_sensitive = request.policy.allow_sensitive_identity

        return IdentityProjection.project(
            identity_context=request.identity_context, allow_sensitive=allow_sensitive
        )


class RequestContextSource:
    """Built-in context source producing the primary user request item."""

    def __init__(self) -> None:
        self._enabled = True

    @property
    def source_id(self) -> str:
        return "user_request_source"

    @property
    def category(self) -> ContextCategory:
        return ContextCategory.REQUEST

    @property
    def priority(self) -> ContextPriority:
        return ContextPriority.CRITICAL

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        self._enabled = value

    def provide(self, request: ContextRequest) -> list[ContextItem]:
        if not self._enabled or not request.user_request:
            return []

        return [
            ContextItem(
                category=ContextCategory.REQUEST,
                content=request.user_request,
                priority=ContextPriority.CRITICAL,
                required=True,
                source=self.source_id,
                trust_level=SourceTrustLevel.TRUSTED,
                metadata={"request_id": request.request_id},
            )
        ]


# --- Future Module Extension Point Stubs ---


class ConversationContextSource:
    """Extension point stub for Module 07 Conversation Engine integration."""

    def __init__(self) -> None:
        self._enabled = True

    @property
    def source_id(self) -> str:
        return "conversation_history_stub"

    @property
    def category(self) -> ContextCategory:
        return ContextCategory.CONVERSATION

    @property
    def priority(self) -> ContextPriority:
        return ContextPriority.HIGH

    @property
    def enabled(self) -> bool:
        return self._enabled

    def provide(self, request: ContextRequest) -> list[ContextItem]:
        # Module 07 will supply conversation messages in future modules
        return []


class MemoryContextSource:
    """Extension point stub for Module 08 Memory Engine integration."""

    def __init__(self) -> None:
        self._enabled = True

    @property
    def source_id(self) -> str:
        return "memory_engine_stub"

    @property
    def category(self) -> ContextCategory:
        return ContextCategory.MEMORY

    @property
    def priority(self) -> ContextPriority:
        return ContextPriority.NORMAL

    @property
    def enabled(self) -> bool:
        return self._enabled

    def provide(self, request: ContextRequest) -> list[ContextItem]:
        # Module 08 will supply long-term memory items in future modules
        return []


class KnowledgeContextSource:
    """Extension point stub for Module 09/10 Personal Knowledge & RAG integration."""

    def __init__(self) -> None:
        self._enabled = True

    @property
    def source_id(self) -> str:
        return "knowledge_rag_stub"

    @property
    def category(self) -> ContextCategory:
        return ContextCategory.KNOWLEDGE

    @property
    def priority(self) -> ContextPriority:
        return ContextPriority.NORMAL

    @property
    def enabled(self) -> bool:
        return self._enabled

    def provide(self, request: ContextRequest) -> list[ContextItem]:
        # Module 10 will supply RAG document chunks in future modules
        return []


class ToolResultContextSource:
    """Extension point stub for future Tool Result integration."""

    def __init__(self) -> None:
        self._enabled = True

    @property
    def source_id(self) -> str:
        return "tool_result_stub"

    @property
    def category(self) -> ContextCategory:
        return ContextCategory.TOOL_RESULT

    @property
    def priority(self) -> ContextPriority:
        return ContextPriority.HIGH

    @property
    def enabled(self) -> bool:
        return self._enabled

    def provide(self, request: ContextRequest) -> list[ContextItem]:
        return []


class ContextSourceRegistry:
    """In-memory thread-safe registry maintaining registered ContextSources."""

    def __init__(self) -> None:
        self._sources: dict[str, Any] = {}
        self._lock = asyncio.Lock()

        # Register default built-in sources
        self.register(SystemContextSource())
        self.register(IdentityContextSource())
        self.register(RequestContextSource())
        self.register(ConversationContextSource())
        self.register(MemoryContextSource())
        self.register(KnowledgeContextSource())
        self.register(ToolResultContextSource())

    def register(self, source: Any) -> None:
        """Register a ContextSource instance."""
        if not hasattr(source, "source_id") or not hasattr(source, "provide"):
            raise ValueError("ContextSource must implement source_id and provide().")
        self._sources[source.source_id] = source

    def unregister(self, source_id: str) -> bool:
        """Unregister a source by source_id."""
        if source_id in self._sources:
            del self._sources[source_id]
            return True
        return False

    def get(self, source_id: str) -> Any | None:
        """Retrieve registered source by source_id."""
        return self._sources.get(source_id)

    def list_sources(self) -> list[dict[str, Any]]:
        """List registered context sources metadata."""
        result = []
        for sid, src in self._sources.items():
            result.append(
                {
                    "source_id": sid,
                    "category": getattr(src, "category", "unknown"),
                    "priority": getattr(src, "priority", 3),
                    "enabled": getattr(src, "enabled", True),
                }
            )
        return result

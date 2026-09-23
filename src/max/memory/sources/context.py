"""MemoryContextSource adapter for Module 06 Context Management integration."""

from max.context.domain.enums import ContextCategory, ContextPriority, SourceTrustLevel
from max.context.domain.item import ContextItem
from max.context.domain.request import ContextRequest
from max.memory.domain.enums import MemoryImportance, MemoryStatus
from max.memory.domain.memory import Memory


class MemoryContextSource:
    """ContextSource adapter supplying persistent long-term memories to ContextManager."""

    def __init__(self, default_memories: list[Memory] | None = None) -> None:
        self._enabled = True
        self._default_memories = default_memories or []

    @property
    def source_id(self) -> str:
        """Unique identifier for this ContextSource."""
        return "memory_engine"

    @property
    def category(self) -> ContextCategory:
        """Context category taxonomy."""
        return ContextCategory.MEMORY

    @property
    def priority(self) -> ContextPriority:
        """Default priority level for memory context items."""
        return ContextPriority.NORMAL

    @property
    def enabled(self) -> bool:
        """Flag indicating whether this source is active."""
        return self._enabled

    def provide(self, request: ContextRequest) -> list[ContextItem]:
        """Convert memory records into candidate ContextItem instances."""

        memories: list[Memory] = []

        # 1. Check for explicit memories passed in source_options
        raw_mems = request.source_options.get("memories") or request.source_options.get(
            "memory_items"
        )
        if raw_mems:
            if isinstance(raw_mems, list):
                for m in raw_mems:
                    if isinstance(m, Memory):
                        memories.append(m)
                    elif isinstance(m, dict):
                        memories.append(Memory(**m))
        elif self._default_memories:
            memories = self._default_memories

        # Convert to ContextItems (excluding expired/deleted memories)
        items: list[ContextItem] = []
        for mem in memories:
            if mem.status in (MemoryStatus.DELETED, MemoryStatus.EXPIRED):
                continue

            # High importance memories receive HIGH context priority
            prio = (
                ContextPriority.HIGH
                if mem.importance in (MemoryImportance.HIGH, MemoryImportance.CRITICAL)
                else ContextPriority.NORMAL
            )

            # Estimate tokens (~4 characters per token)
            token_est = max(1, len(mem.content.text) // 4)

            items.append(
                ContextItem(
                    context_id=f"mem_{mem.memory_id}",
                    category=ContextCategory.MEMORY,
                    content=mem.content.text,
                    priority=prio,
                    required=False,
                    source=self.source_id,
                    token_estimate=token_est,
                    trust_level=SourceTrustLevel.TRUSTED,
                    metadata={
                        "memory_id": str(mem.memory_id),
                        "type": mem.type.value,
                        "importance": mem.importance.value,
                        "confidence": mem.confidence.value,
                        "tags": mem.metadata.tags,
                    },
                )
            )

        return items

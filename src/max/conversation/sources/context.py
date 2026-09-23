"""ConversationContextSource adapter for Module 06 Context Management integration."""

from max.context.domain.enums import ContextCategory, ContextPriority, SourceTrustLevel
from max.context.domain.item import ContextItem
from max.context.domain.request import ContextRequest
from max.conversation.domain.enums import MessageStatus
from max.conversation.domain.message import Message


class ConversationContextSource:
    """ContextSource adapter supplying past conversation messages to ContextManager."""

    def __init__(self, default_messages: list[Message] | None = None) -> None:
        self._enabled = True
        self._default_messages = default_messages or []

    @property
    def source_id(self) -> str:
        """Unique identifier for this ContextSource."""
        return "conversation_history"

    @property
    def category(self) -> ContextCategory:
        """Context category taxonomy."""
        return ContextCategory.CONVERSATION

    @property
    def priority(self) -> ContextPriority:
        """Default priority level for conversation history items."""
        return ContextPriority.HIGH

    @property
    def enabled(self) -> bool:
        """Flag indicating whether this source is active."""
        return self._enabled

    def provide(self, request: ContextRequest) -> list[ContextItem]:
        """Convert prior conversation history into candidate ContextItem instances."""

        messages: list[Message] = []

        # 1. Check for explicit messages passed in source_options
        raw_msgs = request.source_options.get(
            "conversation_messages"
        ) or request.source_options.get("messages")
        if raw_msgs:
            if isinstance(raw_msgs, list):
                for m in raw_msgs:
                    if isinstance(m, Message):
                        messages.append(m)
                    elif isinstance(m, dict):
                        messages.append(Message(**m))
        elif self._default_messages:
            messages = self._default_messages

        # Convert to ContextItems (excluding failed/cancelled messages)
        items: list[ContextItem] = []
        for msg in messages:
            if msg.status not in (
                MessageStatus.COMPLETED,
                MessageStatus.PROCESSING,
                MessageStatus.PENDING,
            ):
                continue

            # Estimate tokens (~4 characters per token)
            token_est = max(1, len(msg.content) // 4)

            items.append(
                ContextItem(
                    context_id=f"conv_msg_{msg.message_id}",
                    category=ContextCategory.CONVERSATION,
                    content=msg.content,
                    priority=ContextPriority.HIGH
                    if msg.sequence > len(messages) - 5
                    else ContextPriority.NORMAL,
                    required=False,
                    source=self.source_id,
                    token_estimate=token_est,
                    trust_level=SourceTrustLevel.TRUSTED,
                    metadata={
                        "role": msg.role.value,
                        "sequence": msg.sequence,
                        "message_id": str(msg.message_id),
                        "created_at": msg.created_at.isoformat(),
                    },
                )
            )

        return items

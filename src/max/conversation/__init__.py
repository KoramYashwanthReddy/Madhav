"""Module 07 — Conversation Engine for MAX Personal AI platform."""

from max.conversation.domain import (
    Conversation,
    ConversationHistory,
    ConversationSettingsModel,
    ConversationStatus,
    ConversationSummary,
    Message,
    MessageRole,
    MessageStatus,
)
from max.conversation.exceptions import (
    ConversationAccessError,
    ConversationArchivedError,
    ConversationDeletedError,
    ConversationEngineError,
    ConversationNotFoundError,
    ConversationPersistenceError,
    ConversationTurnError,
    DuplicateMessageError,
    InvalidConversationStateError,
    MessageNotFoundError,
    MessageValidationError,
)
from max.conversation.repositories import (
    ConversationRepository,
    InMemoryConversationRepository,
)
from max.conversation.services import (
    ConversationService,
    ConversationTurnService,
    DeterministicTitleGenerator,
    TurnResult,
)
from max.conversation.sources import ConversationContextSource

__all__ = [
    "Conversation",
    "ConversationAccessError",
    "ConversationArchivedError",
    "ConversationContextSource",
    "ConversationDeletedError",
    "ConversationEngineError",
    "ConversationHistory",
    "ConversationNotFoundError",
    "ConversationPersistenceError",
    "ConversationRepository",
    "ConversationService",
    "ConversationSettingsModel",
    "ConversationStatus",
    "ConversationSummary",
    "ConversationTurnError",
    "ConversationTurnService",
    "DeterministicTitleGenerator",
    "DuplicateMessageError",
    "InMemoryConversationRepository",
    "InvalidConversationStateError",
    "Message",
    "MessageNotFoundError",
    "MessageRole",
    "MessageStatus",
    "MessageValidationError",
    "TurnResult",
]

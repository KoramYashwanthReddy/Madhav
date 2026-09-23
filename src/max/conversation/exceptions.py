"""Conversation Engine subsystem custom exceptions."""

from typing import Any

from max.core.exceptions import MaxException


class ConversationEngineError(MaxException):
    """Base exception for all Conversation Engine failures."""

    def __init__(
        self,
        message: str = "A conversation processing error occurred.",
        code: str = "CONVERSATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ConversationNotFoundError(ConversationEngineError):
    """Raised when a requested conversation is not found."""

    def __init__(
        self,
        message: str = "Conversation not found.",
        code: str = "CONVERSATION_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ConversationDeletedError(ConversationEngineError):
    """Raised when an operation is performed on a deleted conversation."""

    def __init__(
        self,
        message: str = "Conversation has been deleted.",
        code: str = "CONVERSATION_DELETED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ConversationArchivedError(ConversationEngineError):
    """Raised when a new message or active operation is performed on an archived conversation."""

    def __init__(
        self,
        message: str = "Conversation is archived.",
        code: str = "CONVERSATION_ARCHIVED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidConversationStateError(ConversationEngineError):
    """Raised when an invalid state transition is requested."""

    def __init__(
        self,
        message: str = "Invalid conversation state transition.",
        code: str = "INVALID_CONVERSATION_STATE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class MessageNotFoundError(ConversationEngineError):
    """Raised when a requested message is not found."""

    def __init__(
        self,
        message: str = "Message not found.",
        code: str = "MESSAGE_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class MessageValidationError(ConversationEngineError):
    """Raised when message content or parameters fail validation."""

    def __init__(
        self,
        message: str = "Message validation failed.",
        code: str = "MESSAGE_VALIDATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 422,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class DuplicateMessageError(ConversationEngineError):
    """Raised when a client_message_id idempotent conflict occurs."""

    def __init__(
        self,
        message: str = "Duplicate client message ID provided.",
        code: str = "DUPLICATE_MESSAGE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ConversationAccessError(ConversationEngineError):
    """Raised when an identity attempts to access a conversation owned by another identity."""

    def __init__(
        self,
        message: str = "Access to conversation denied.",
        code: str = "CONVERSATION_ACCESS_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ConversationPersistenceError(ConversationEngineError):
    """Raised when an underlying repository persistence operation fails."""

    def __init__(
        self,
        message: str = "Conversation persistence operation failed.",
        code: str = "CONVERSATION_PERSISTENCE_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ConversationTurnError(ConversationEngineError):
    """Raised when an end-to-end conversation turn processing fails."""

    def __init__(
        self,
        message: str = "Conversation turn processing failed.",
        code: str = "CONVERSATION_TURN_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)

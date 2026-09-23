"""Personal Knowledge Engine subsystem custom exceptions."""

from typing import Any

from madhav.core.exceptions import MadhavException


class KnowledgeError(MadhavException):
    """Base exception for all Personal Knowledge Engine failures."""

    def __init__(
        self,
        message: str = "A personal knowledge engine processing error occurred.",
        code: str = "KNOWLEDGE_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class KnowledgeEntityNotFoundError(KnowledgeError):
    """Raised when a requested knowledge entity is not found."""

    def __init__(
        self,
        message: str = "Knowledge entity not found.",
        code: str = "KNOWLEDGE_ENTITY_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class KnowledgeFactNotFoundError(KnowledgeError):
    """Raised when a requested knowledge fact is not found."""

    def __init__(
        self,
        message: str = "Knowledge fact not found.",
        code: str = "KNOWLEDGE_FACT_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class KnowledgeRelationNotFoundError(KnowledgeError):
    """Raised when a requested knowledge relation is not found."""

    def __init__(
        self,
        message: str = "Knowledge relation not found.",
        code: str = "KNOWLEDGE_RELATION_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class KnowledgeCollectionNotFoundError(KnowledgeError):
    """Raised when a requested knowledge collection is not found."""

    def __init__(
        self,
        message: str = "Knowledge collection not found.",
        code: str = "KNOWLEDGE_COLLECTION_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class KnowledgeOwnershipError(KnowledgeError):
    """Raised when an identity attempts to access or mutate knowledge owned by another identity."""

    def __init__(
        self,
        message: str = "Access to knowledge item denied due to owner mismatch.",
        code: str = "KNOWLEDGE_OWNERSHIP_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class KnowledgeValidationError(KnowledgeError):
    """Raised when knowledge fields fail domain validation rules."""

    def __init__(
        self,
        message: str = "Knowledge validation failed.",
        code: str = "KNOWLEDGE_VALIDATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 422,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class DuplicateKnowledgeError(KnowledgeError):
    """Raised when creating a duplicate entity, fact, or collection."""

    def __init__(
        self,
        message: str = "A duplicate knowledge item already exists.",
        code: str = "DUPLICATE_KNOWLEDGE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidKnowledgeStateTransitionError(KnowledgeError):
    """Raised when an invalid lifecycle state transition is requested."""

    def __init__(
        self,
        message: str = "Invalid knowledge lifecycle state transition.",
        code: str = "INVALID_KNOWLEDGE_STATE_TRANSITION",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidKnowledgeRelationError(KnowledgeError):
    """Raised when creating a relation with invalid source/target entities."""

    def __init__(
        self,
        message: str = "Invalid knowledge relationship endpoints.",
        code: str = "INVALID_KNOWLEDGE_RELATION",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidFactValueError(KnowledgeError):
    """Raised when fact value fails type validation against value_type."""

    def __init__(
        self,
        message: str = "Fact value does not conform to declared value_type.",
        code: str = "INVALID_FACT_VALUE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 422,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)

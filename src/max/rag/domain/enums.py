"""Domain enums for RAG & Retrieval Engine."""

from enum import StrEnum


class DocumentType(StrEnum):
    """Supported document format types."""

    TEXT = "TEXT"
    MARKDOWN = "MARKDOWN"
    PDF = "PDF"
    WEB_PAGE = "WEB_PAGE"
    KNOWLEDGE_EXPORT = "KNOWLEDGE_EXPORT"
    IMPORTED_NOTES = "IMPORTED_NOTES"
    STRUCTURED_TEXT = "STRUCTURED_TEXT"


class DocumentStatus(StrEnum):
    """Document lifecycle state."""

    ACTIVE = "ACTIVE"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class DocumentSourceType(StrEnum):
    """Provenance source type for indexed documents."""

    FILE = "FILE"
    TEXT = "TEXT"
    URL = "URL"
    MEMORY = "MEMORY"
    PERSONAL_KNOWLEDGE = "PERSONAL_KNOWLEDGE"
    MANUAL = "MANUAL"
    IMPORT = "IMPORT"
    FUTURE_EXTERNAL_SOURCE = "FUTURE_EXTERNAL_SOURCE"

"""Domain enumerations for Module 24 — Document Intelligence."""

from enum import StrEnum


class DocumentType(StrEnum):
    """Broad semantic categories for supported documents."""

    PDF = "PDF"
    WORD = "WORD"
    SPREADSHEET = "SPREADSHEET"
    PRESENTATION = "PRESENTATION"
    TEXT = "TEXT"
    MARKDOWN = "MARKDOWN"
    CSV = "CSV"
    JSON = "JSON"
    XML = "XML"
    UNKNOWN = "UNKNOWN"


class DocumentFormat(StrEnum):
    """Exact file format extensions."""

    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    TXT = "txt"
    MD = "md"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    UNKNOWN = "unknown"


class DocumentStatus(StrEnum):
    """Lifecycle states for a managed Document."""

    DISCOVERED = "DISCOVERED"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    PARTIALLY_PROCESSED = "PARTIALLY_PROCESSED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class DocumentSource(StrEnum):
    """Origin reference type for document acquisition."""

    LOCAL_FILE = "LOCAL_FILE"
    CONTROLLED_UPLOAD = "CONTROLLED_UPLOAD"
    WEB_DOCUMENT = "WEB_DOCUMENT"
    MEMORY_REFERENCE = "MEMORY_REFERENCE"
    KNOWLEDGE_REFERENCE = "KNOWLEDGE_REFERENCE"
    TEMPORARY_DOCUMENT = "TEMPORARY_DOCUMENT"


class ElementType(StrEnum):
    """Granular structural element classifications."""

    PAGE = "PAGE"
    SECTION = "SECTION"
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    LIST = "LIST"
    LIST_ITEM = "LIST_ITEM"
    TABLE = "TABLE"
    TABLE_ROW = "TABLE_ROW"
    TABLE_CELL = "TABLE_CELL"
    SHEET = "SHEET"
    SLIDE = "SLIDE"
    CODE_BLOCK = "CODE_BLOCK"
    HYPERLINK = "HYPERLINK"
    IMAGE_METADATA = "IMAGE_METADATA"
    CUSTOM = "CUSTOM"


class ProcessingStatus(StrEnum):
    """Detailed operational status for document processing jobs."""

    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    PARSING = "PARSING"
    EXTRACTING = "EXTRACTING"
    NORMALIZING = "NORMALIZING"
    VALIDATING_RESULT = "VALIDATING_RESULT"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ComparisonChangeType(StrEnum):
    """Types of diff changes detected between document versions."""

    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"
    MOVED = "MOVED"
    UNCHANGED = "UNCHANGED"

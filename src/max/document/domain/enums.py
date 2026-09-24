"""Domain enumerations for Module 24 — Document Intelligence."""

from enum import Enum


class DocumentType(str, Enum):
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


class DocumentFormat(str, Enum):
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


class DocumentStatus(str, Enum):
    """Lifecycle states for a managed Document."""

    DISCOVERED = "DISCOVERED"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    PARTIALLY_PROCESSED = "PARTIALLY_PROCESSED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class DocumentSource(str, Enum):
    """Origin reference type for document acquisition."""

    LOCAL_FILE = "LOCAL_FILE"
    CONTROLLED_UPLOAD = "CONTROLLED_UPLOAD"
    WEB_DOCUMENT = "WEB_DOCUMENT"
    MEMORY_REFERENCE = "MEMORY_REFERENCE"
    KNOWLEDGE_REFERENCE = "KNOWLEDGE_REFERENCE"
    TEMPORARY_DOCUMENT = "TEMPORARY_DOCUMENT"


class ElementType(str, Enum):
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


class ProcessingStatus(str, Enum):
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


class ComparisonChangeType(str, Enum):
    """Types of diff changes detected between document versions."""

    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"
    MOVED = "MOVED"
    UNCHANGED = "UNCHANGED"

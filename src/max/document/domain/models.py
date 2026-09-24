"""Domain models for Module 24 — Document Intelligence."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.document.domain.enums import (
    ComparisonChangeType,
    DocumentFormat,
    DocumentSource,
    DocumentStatus,
    DocumentType,
    ElementType,
    ProcessingStatus,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


# ----------------------------------------------------------------------
# Location & Metadata
# ----------------------------------------------------------------------


class DocumentLocation(BaseModel):
    """Position pointer within a document format."""

    page_number: int | None = Field(default=None, description="1-indexed page number")
    section_id: str | None = Field(default=None, description="Parent section ID")
    sheet_name: str | None = Field(default=None, description="Spreadsheet sheet name")
    row_index: int | None = Field(default=None, description="0-indexed row index")
    column_index: int | None = Field(default=None, description="0-indexed column index")
    slide_number: int | None = Field(default=None, description="1-indexed slide number")
    bounding_box: list[float] | None = Field(
        default=None, description="Optional bounding box coordinates [x0, y0, x1, y1]"
    )


class DocumentMetadata(BaseModel):
    """Extracted and calculated document properties."""

    filename: str = Field(..., description="Original or display filename")
    normalized_filename: str = Field(..., description="Sanitized filename")
    mime_type: str = Field(default="application/octet-stream", description="Detected MIME type")
    file_size_bytes: int = Field(..., description="File size in bytes")
    content_hash: str = Field(..., description="SHA-256 hash of raw document bytes")
    author: str | None = Field(default=None, description="Document author name")
    creator: str | None = Field(default=None, description="Software application that created document")
    title: str | None = Field(default=None, description="Document title")
    subject: str | None = Field(default=None, description="Document subject/topic")
    keywords: list[str] = Field(default_factory=list, description="Extracted keywords")
    creation_date: datetime | None = Field(default=None, description="Document creation timestamp")
    modification_date: datetime | None = Field(default=None, description="Document modification timestamp")
    page_count: int = Field(default=0, description="Total pages")
    word_count: int = Field(default=0, description="Total word count")
    character_count: int = Field(default=0, description="Total character count")
    sheet_count: int = Field(default=0, description="Total spreadsheet sheets")
    slide_count: int = Field(default=0, description="Total presentation slides")
    custom_properties: dict[str, Any] = Field(
        default_factory=dict, description="Additional format-specific metadata"
    )


# ----------------------------------------------------------------------
# Elements & Normalized Structure
# ----------------------------------------------------------------------


class DocumentElement(BaseModel):
    """Single extracted structural unit of a document."""

    element_id: str = Field(
        default_factory=lambda: f"elem_{uuid.uuid4().hex[:12]}",
        description="Unique element identifier",
    )
    document_id: str = Field(..., description="Parent document ID")
    version_id: str = Field(..., description="Associated version ID")
    element_type: ElementType = Field(..., description="Type of structural element")
    content: str = Field(..., description="Extracted textual or structural content")
    location: DocumentLocation = Field(
        default_factory=DocumentLocation, description="Location within document"
    )
    parent_id: str | None = Field(default=None, description="Parent element ID if nested")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Format-specific element metadata"
    )
    source_reference: str | None = Field(default=None, description="Source provenance marker")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")


class DocumentPage(BaseModel):
    """Extracted page representation."""

    page_number: int = Field(..., description="1-indexed page number")
    text: str = Field(default="", description="Full text extracted from page")
    element_ids: list[str] = Field(default_factory=list, description="IDs of elements on page")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Page metadata")


class DocumentSection(BaseModel):
    """Extracted document section representation."""

    section_id: str = Field(
        default_factory=lambda: f"sec_{uuid.uuid4().hex[:12]}",
        description="Unique section ID",
    )
    title: str = Field(default="", description="Section title or heading")
    level: int = Field(default=1, description="Heading depth level (1=H1, 2=H2, ...)")
    content: str = Field(default="", description="Section text content")
    parent_section_id: str | None = Field(default=None, description="Parent section ID")


class DocumentHeading(BaseModel):
    """Extracted heading representation."""

    heading_id: str = Field(
        default_factory=lambda: f"hdg_{uuid.uuid4().hex[:12]}",
        description="Unique heading ID",
    )
    text: str = Field(..., description="Heading text")
    level: int = Field(default=1, description="Heading level")
    location: DocumentLocation = Field(default_factory=DocumentLocation)


class DocumentParagraph(BaseModel):
    """Extracted paragraph representation."""

    paragraph_id: str = Field(
        default_factory=lambda: f"para_{uuid.uuid4().hex[:12]}",
        description="Unique paragraph ID",
    )
    text: str = Field(..., description="Paragraph text")
    location: DocumentLocation = Field(default_factory=DocumentLocation)


class DocumentList(BaseModel):
    """Extracted list representation."""

    list_id: str = Field(
        default_factory=lambda: f"lst_{uuid.uuid4().hex[:12]}",
        description="Unique list ID",
    )
    items: list[str] = Field(default_factory=list, description="List item texts")
    ordered: bool = Field(default=False, description="True if ordered/numbered list")
    location: DocumentLocation = Field(default_factory=DocumentLocation)


class DocumentTableCell(BaseModel):
    """Cell within a document table."""

    row_index: int = Field(..., description="0-indexed row index")
    column_index: int = Field(..., description="0-indexed column index")
    content: str = Field(default="", description="Cell text content")
    row_span: int = Field(default=1, description="Cell row span")
    col_span: int = Field(default=1, description="Cell column span")
    is_header: bool = Field(default=False, description="True if cell is a header")


class DocumentTableRow(BaseModel):
    """Row within a document table."""

    row_index: int = Field(..., description="0-indexed row index")
    cells: list[DocumentTableCell] = Field(default_factory=list, description="Row cells")


class DocumentTable(BaseModel):
    """Extracted table representation."""

    table_id: str = Field(
        default_factory=lambda: f"tbl_{uuid.uuid4().hex[:12]}",
        description="Unique table ID",
    )
    caption: str | None = Field(default=None, description="Optional table caption/title")
    headers: list[str] = Field(default_factory=list, description="Column header names")
    rows: list[DocumentTableRow] = Field(default_factory=list, description="Table rows")
    row_count: int = Field(default=0, description="Total row count")
    column_count: int = Field(default=0, description="Total column count")
    location: DocumentLocation = Field(default_factory=DocumentLocation)


class DocumentSheet(BaseModel):
    """Sheet within a spreadsheet document."""

    sheet_name: str = Field(..., description="Sheet name")
    sheet_index: int = Field(default=0, description="0-indexed sheet index")
    tables: list[DocumentTable] = Field(default_factory=list, description="Tables on sheet")
    row_count: int = Field(default=0, description="Sheet row count")
    column_count: int = Field(default=0, description="Sheet column count")
    text_preview: str = Field(default="", description="First few rows as text preview")


class DocumentSlide(BaseModel):
    """Slide within a presentation document."""

    slide_number: int = Field(..., description="1-indexed slide number")
    title: str = Field(default="", description="Slide title")
    text_blocks: list[str] = Field(default_factory=list, description="Text blocks on slide")
    speaker_notes: str = Field(default="", description="Speaker notes")
    tables: list[DocumentTable] = Field(default_factory=list, description="Tables on slide")


class DocumentStructure(BaseModel):
    """Unified normalized document hierarchy."""

    pages: list[DocumentPage] = Field(default_factory=list)
    sections: list[DocumentSection] = Field(default_factory=list)
    headings: list[DocumentHeading] = Field(default_factory=list)
    paragraphs: list[DocumentParagraph] = Field(default_factory=list)
    lists: list[DocumentList] = Field(default_factory=list)
    tables: list[DocumentTable] = Field(default_factory=list)
    sheets: list[DocumentSheet] = Field(default_factory=list)
    slides: list[DocumentSlide] = Field(default_factory=list)
    elements: list[DocumentElement] = Field(default_factory=list)


# ----------------------------------------------------------------------
# Provenance & Citation
# ----------------------------------------------------------------------


class DocumentCitation(BaseModel):
    """Structured citation marker pointing to specific document content."""

    citation_id: str = Field(
        default_factory=lambda: f"cite_{uuid.uuid4().hex[:12]}",
        description="Unique citation ID",
    )
    document_id: str = Field(..., description="Source document ID")
    version_id: str = Field(..., description="Source document version ID")
    element_id: str | None = Field(default=None, description="Element ID referenced")
    filename: str = Field(..., description="Source filename")
    location: DocumentLocation = Field(default_factory=DocumentLocation)
    excerpt: str = Field(..., description="Extracted text excerpt")
    formatted_citation: str = Field(..., description="Human-readable citation string")


class DocumentProvenance(BaseModel):
    """Immutable origin and processing trace for extracted information."""

    document_id: str = Field(..., description="Target document ID")
    version_id: str = Field(..., description="Version ID")
    source_type: DocumentSource = Field(..., description="Source type")
    source_reference: str = Field(..., description="Original path or URL")
    content_hash: str = Field(..., description="Content SHA-256 hash")
    processed_at: datetime = Field(default_factory=_utc_now)
    parser_name: str = Field(..., description="Parser identifier used")


# ----------------------------------------------------------------------
# Versions & Document Record
# ----------------------------------------------------------------------


class DocumentVersion(BaseModel):
    """Historical snapshot of a document content and structure."""

    version_id: str = Field(
        default_factory=lambda: f"dver_{uuid.uuid4().hex[:12]}",
        description="Unique version ID",
    )
    document_id: str = Field(..., description="Parent document ID")
    version_number: int = Field(default=1, description="Sequential version index")
    content_hash: str = Field(..., description="SHA-256 hash of version content")
    file_size_bytes: int = Field(..., description="File size in bytes")
    change_summary: str = Field(default="", description="Summary of version changes")
    previous_version_id: str | None = Field(default=None, description="Previous version ID")
    created_at: datetime = Field(default_factory=_utc_now)


class Document(BaseModel):
    """Root managed document entity."""

    id: str = Field(
        default_factory=lambda: f"doc_{uuid.uuid4().hex[:12]}",
        description="Unique document identifier",
    )
    owner_id: str = Field(default="user_default", description="Owner identifier")
    source_type: DocumentSource = Field(..., description="Source origin category")
    source_reference: str = Field(..., description="File path, URL, or reference URI")
    filename: str = Field(..., description="Document display filename")
    normalized_filename: str = Field(..., description="Sanitized filename")
    format: DocumentFormat = Field(..., description="Detected format extension")
    doc_type: DocumentType = Field(..., description="Semantic document category")
    content_hash: str = Field(..., description="SHA-256 content hash")
    status: DocumentStatus = Field(default=DocumentStatus.DISCOVERED)
    current_version_id: str | None = Field(default=None)
    metadata: DocumentMetadata | None = Field(default=None)
    structure: DocumentStructure | None = Field(default=None)
    raw_text: str = Field(default="", description="Full extracted raw text")
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


# ----------------------------------------------------------------------
# Diff & Comparison
# ----------------------------------------------------------------------


class DocumentChange(BaseModel):
    """Atomic change entry in document comparison."""

    change_id: str = Field(
        default_factory=lambda: f"chg_{uuid.uuid4().hex[:12]}",
        description="Unique change ID",
    )
    change_type: ComparisonChangeType = Field(..., description="Change classification")
    location: str = Field(..., description="Location path (e.g. section, paragraph, cell)")
    old_value: str | None = Field(default=None, description="Original content")
    new_value: str | None = Field(default=None, description="New content")


class DocumentComparison(BaseModel):
    """Machine-readable diff result between two documents/versions."""

    comparison_id: str = Field(
        default_factory=lambda: f"comp_{uuid.uuid4().hex[:12]}",
        description="Unique comparison ID",
    )
    source_document_id: str = Field(..., description="Base document ID")
    target_document_id: str = Field(..., description="Comparison target document ID")
    source_version_id: str = Field(..., description="Base version ID")
    target_version_id: str = Field(..., description="Target version ID")
    changes: list[DocumentChange] = Field(default_factory=list, description="Extracted changes")
    added_count: int = Field(default=0)
    removed_count: int = Field(default=0)
    modified_count: int = Field(default=0)
    summary: str = Field(default="", description="Human-readable diff summary")
    compared_at: datetime = Field(default_factory=_utc_now)


# ----------------------------------------------------------------------
# Processing Jobs & Extraction Results
# ----------------------------------------------------------------------


class DocumentProcessingError(BaseModel):
    """Structured error record during processing."""

    error_type: str = Field(..., description="Error exception class name")
    message: str = Field(..., description="Human-readable error description")
    occurred_at: datetime = Field(default_factory=_utc_now)


class DocumentProcessingJob(BaseModel):
    """Tracking record for background document processing."""

    job_id: str = Field(
        default_factory=lambda: f"job_{uuid.uuid4().hex[:12]}",
        description="Unique job ID",
    )
    document_id: str = Field(..., description="Target document ID")
    status: ProcessingStatus = Field(default=ProcessingStatus.QUEUED)
    error: DocumentProcessingError | None = Field(default=None)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)


class DocumentExtractionResult(BaseModel):
    """Result payload from parser extraction pipeline."""

    document_id: str = Field(..., description="Target document ID")
    metadata: DocumentMetadata = Field(..., description="Extracted metadata")
    structure: DocumentStructure = Field(..., description="Extracted structure")
    raw_text: str = Field(..., description="Full text")
    provenance: DocumentProvenance = Field(..., description="Extraction provenance")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal extraction warnings")


class DocumentSummary(BaseModel):
    """Compact summary overview of document content."""

    document_id: str = Field(..., description="Target document ID")
    title: str = Field(default="", description="Document title")
    doc_type: DocumentType = Field(..., description="Document type")
    format: DocumentFormat = Field(..., description="Document format")
    summary_text: str = Field(..., description="Brief content summary")
    key_sections: list[str] = Field(default_factory=list, description="Main section headers")
    table_count: int = Field(default=0)
    page_count: int = Field(default=0)
    word_count: int = Field(default=0)


# ----------------------------------------------------------------------
# Search, Conversion, Generation & Validation
# ----------------------------------------------------------------------


class DocumentSearchRequest(BaseModel):
    """Deterministic text search request across documents."""

    query: str = Field(..., description="Search query string")
    document_ids: list[str] | None = Field(default=None, description="Optional document filter")
    doc_types: list[DocumentType] | None = Field(default=None, description="Optional doc type filter")
    case_sensitive: bool = Field(default=False, description="Case sensitivity option")
    max_results: int = Field(default=20, ge=1, le=100)


class DocumentSearchResult(BaseModel):
    """Single search match result."""

    document_id: str = Field(..., description="Matched document ID")
    filename: str = Field(..., description="Matched document filename")
    element_id: str | None = Field(default=None, description="Matched element ID")
    location: DocumentLocation = Field(default_factory=DocumentLocation)
    matched_text: str = Field(..., description="Exact string match segment")
    context: str = Field(..., description="Surrounding text window")
    citation: DocumentCitation = Field(..., description="Provenance citation")


class DocumentSearchResponse(BaseModel):
    """Search query response wrapper."""

    query: str = Field(..., description="Original search query")
    total_matches: int = Field(..., description="Total matches found")
    results: list[DocumentSearchResult] = Field(default_factory=list)


class DocumentConversionRequest(BaseModel):
    """Request to convert a document representation into another format."""

    source_document_id: str = Field(..., description="Source document ID")
    target_format: DocumentFormat = Field(..., description="Target format extension")
    output_filename: str | None = Field(default=None, description="Optional target filename")


class DocumentConversionResult(BaseModel):
    """Result of a document format conversion."""

    source_document_id: str = Field(..., description="Source document ID")
    target_document_id: str = Field(..., description="Converted document ID")
    target_format: DocumentFormat = Field(..., description="Target format")
    output_path: str = Field(..., description="Path to converted document")
    content_hash: str = Field(..., description="SHA-256 hash of output document")


class DocumentGenerationRequest(BaseModel):
    """Request to generate a new document from structured content."""

    target_format: DocumentFormat = Field(..., description="Target output format")
    title: str = Field(..., description="Document title")
    filename: str = Field(..., description="Target output filename")
    content_markdown: str = Field(..., description="Structured Markdown content to generate from")
    tables: list[DocumentTable] | None = Field(default=None, description="Optional structured tables")
    owner_id: str = Field(default="user_default")


class DocumentGenerationResult(BaseModel):
    """Result of a document generation operation."""

    document_id: str = Field(..., description="Generated document ID")
    filename: str = Field(..., description="Generated filename")
    output_path: str = Field(..., description="Filesystem path of generated document")
    format: DocumentFormat = Field(..., description="Generated format")
    content_hash: str = Field(..., description="SHA-256 hash of generated document")
    file_size_bytes: int = Field(..., description="Generated file size")


class DocumentValidationResult(BaseModel):
    """Validation report after parsing or generation."""

    is_valid: bool = Field(..., description="True if validation passed")
    errors: list[str] = Field(default_factory=list, description="Validation failure reasons")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    security_verdict: str = Field(default="PASSED", description="Security check status")

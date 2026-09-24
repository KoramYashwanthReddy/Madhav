"""FastAPI router for Module 24 — Document Intelligence."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from max.document.container import get_document_container
from max.document.domain.enums import DocumentFormat, DocumentSource
from max.document.domain.exceptions import (
    DocumentConversionError,
    DocumentGenerationError,
    DocumentNotFoundError,
    DocumentParseError,
    DocumentSecurityError,
    DocumentTooLargeError,
    DocumentValidationError,
    UnsupportedDocumentFormatError,
)
from max.document.domain.models import (
    Document,
    DocumentComparison,
    DocumentConversionRequest,
    DocumentConversionResult,
    DocumentExtractionResult,
    DocumentGenerationRequest,
    DocumentGenerationResult,
    DocumentMetadata,
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentSummary,
    DocumentValidationResult,
    DocumentVersion,
)

router = APIRouter(prefix="/documents", tags=["Document Intelligence"])


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """Return Document Intelligence subsystem health status."""
    container = get_document_container()
    return {
        "status": "healthy",
        "subsystem": "document_intelligence",
        "enabled": container.settings.enabled,
        "max_file_size_mb": container.settings.max_document_size_mb,
        "supported_formats": [f.value for f in DocumentFormat if f != DocumentFormat.UNKNOWN],
    }


# ---------------------------------------------------------------------------
# Document Registration & Processing
# ---------------------------------------------------------------------------


@router.post("/register", response_model=Document, status_code=status.HTTP_201_CREATED)
async def register_document(
    source_reference: str,
    filename: str,
    source_type: DocumentSource = DocumentSource.LOCAL_FILE,
    owner_id: str = "user_default",
) -> Document:
    """Register a new document by source path or reference.

    Performs multi-signal format detection (extension, MIME, magic bytes).
    Deduplicates by SHA-256 content hash. Does NOT parse — call /process next.
    """
    container = get_document_container()
    try:
        return await container.service.register_document(
            source_reference=source_reference,
            filename=filename,
            source_type=source_type,
            owner_id=owner_id,
        )
    except DocumentTooLargeError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
    except DocumentSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UnsupportedDocumentFormatError as e:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e))


@router.post("/{document_id}/process", response_model=DocumentExtractionResult)
async def process_document(document_id: str) -> DocumentExtractionResult:
    """Parse a registered document and extract structure, metadata, and text.

    Runs prompt injection defense. Creates version 1 snapshot.
    """
    container = get_document_container()
    try:
        return await container.service.process_document(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")
    except DocumentParseError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DocumentSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UnsupportedDocumentFormatError as e:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e))


# ---------------------------------------------------------------------------
# Retrieval & Listings
# ---------------------------------------------------------------------------


@router.get("", response_model=list[Document])
async def list_documents(
    owner_id: str | None = Query(default=None, description="Filter by owner ID"),
    doc_type: str | None = Query(default=None, description="Filter by document type"),
    format_ext: str | None = Query(default=None, description="Filter by format extension"),
) -> list[Document]:
    """List all registered documents with optional filters."""
    container = get_document_container()
    return container.service.list_documents(owner_id=owner_id, doc_type=doc_type, format_ext=format_ext)


@router.get("/{document_id}", response_model=Document)
async def get_document(document_id: str) -> Document:
    """Retrieve a Document entity by ID."""
    container = get_document_container()
    try:
        return container.service.get_document(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")


@router.get("/{document_id}/metadata", response_model=DocumentMetadata)
async def get_document_metadata(document_id: str) -> DocumentMetadata:
    """Get extracted metadata properties of a processed document."""
    container = get_document_container()
    try:
        return container.service.get_metadata(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")
    except DocumentValidationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{document_id}/content", response_model=dict[str, str])
async def get_document_content(document_id: str) -> dict[str, str]:
    """Get full extracted text content of a processed document."""
    container = get_document_container()
    try:
        content = container.service.get_content(document_id)
        return {"document_id": document_id, "content": content}
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")


@router.get("/{document_id}/structure")
async def get_document_structure(document_id: str) -> Any:
    """Get normalized structural hierarchy (sections, headings, tables, slides, sheets)."""
    container = get_document_container()
    try:
        struct = container.service.get_structure(document_id)
        return struct.model_dump()
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")
    except DocumentValidationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{document_id}/summary", response_model=DocumentSummary)
async def get_document_summary(document_id: str) -> DocumentSummary:
    """Get a compact summary overview of a processed document."""
    container = get_document_container()
    try:
        return container.service.get_summary(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(document_id: str) -> dict[str, str]:
    """Remove a document from the document repository."""
    container = get_document_container()
    if container.service.delete_document(document_id):
        return {"document_id": document_id, "status": "DELETED"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------


@router.get("/{document_id}/versions", response_model=list[DocumentVersion])
async def list_document_versions(document_id: str) -> list[DocumentVersion]:
    """List historical version snapshots for a document."""
    container = get_document_container()
    try:
        return container.service.list_versions(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")


@router.get("/versions/{version_id}", response_model=DocumentVersion)
async def get_document_version(version_id: str) -> DocumentVersion:
    """Retrieve a specific document version snapshot by version ID."""
    container = get_document_container()
    try:
        return container.service.get_version(version_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version '{version_id}' not found.")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@router.get("/{document_id}/validate", response_model=DocumentValidationResult)
async def validate_document(document_id: str) -> DocumentValidationResult:
    """Run integrity and security validation on a registered document."""
    container = get_document_container()
    try:
        return container.service.validate_document(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")


# ---------------------------------------------------------------------------
# Search & Comparison
# ---------------------------------------------------------------------------


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(request: DocumentSearchRequest) -> DocumentSearchResponse:
    """Perform deterministic exact-text search across one or more processed documents.

    Returns matches with citations and surrounding context windows.
    """
    container = get_document_container()
    return container.service.search_documents(request)


@router.post("/compare", response_model=DocumentComparison)
async def compare_documents(
    source_document_id: str,
    target_document_id: str,
) -> DocumentComparison:
    """Compute a machine-readable diff between two registered documents."""
    container = get_document_container()
    try:
        return container.service.compare_documents(source_document_id, target_document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# RAG Integration
# ---------------------------------------------------------------------------


@router.post("/{document_id}/rag/prepare", response_model=list[dict[str, Any]])
async def prepare_rag_chunks(document_id: str) -> list[dict[str, Any]]:
    """Prepare RAG chunk candidates from a processed document for Module 10 (RAG Engine).

    Returns structured chunk objects with provenance metadata.
    """
    container = get_document_container()
    try:
        return container.service.prepare_rag(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")


# ---------------------------------------------------------------------------
# Generation & Conversion
# ---------------------------------------------------------------------------


@router.post("/generate", response_model=DocumentGenerationResult, status_code=status.HTTP_201_CREATED)
async def generate_document(
    request: DocumentGenerationRequest,
    output_dir: str = Query(default="./generated_docs", description="Output directory path"),
) -> DocumentGenerationResult:
    """Generate a new document file from structured Markdown content."""
    container = get_document_container()
    try:
        return await container.service.generate_document(request, output_dir)
    except DocumentGenerationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DocumentSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/convert", response_model=DocumentConversionResult, status_code=status.HTTP_201_CREATED)
async def convert_document(
    request: DocumentConversionRequest,
    output_dir: str = Query(default="./converted_docs", description="Output directory path"),
) -> DocumentConversionResult:
    """Convert a registered document from its current format to a target format."""
    container = get_document_container()
    try:
        return await container.service.convert_document(request, output_dir)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{request.source_document_id}' not found.",
        )
    except DocumentConversionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DocumentSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

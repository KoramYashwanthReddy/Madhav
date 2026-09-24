"""Document service facade for Module 24 — Document Intelligence."""

import difflib
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from max.document.adapters.filesystem_adapter import DocumentFilesystemAdapter
from max.document.adapters.rag_adapter import DocumentRAGAdapter
from max.document.converters.base import BaseDocumentConverter
from max.document.domain.enums import (
    ComparisonChangeType,
    DocumentFormat,
    DocumentSource,
    DocumentStatus,
    DocumentType,
    ProcessingStatus,
)
from max.document.domain.exceptions import (
    DocumentNotFoundError,
    DocumentTooLargeError,
    DocumentValidationError,
)
from max.document.domain.models import (
    Document,
    DocumentChange,
    DocumentCitation,
    DocumentComparison,
    DocumentConversionRequest,
    DocumentConversionResult,
    DocumentExtractionResult,
    DocumentGenerationRequest,
    DocumentGenerationResult,
    DocumentMetadata,
    DocumentProcessingError,
    DocumentProcessingJob,
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentSearchResult,
    DocumentSummary,
    DocumentValidationResult,
    DocumentVersion,
)
from max.document.generators.base import BaseDocumentGenerator
from max.document.parsers.registry import DocumentParserRegistry
from max.document.repositories.repositories import (
    DocumentAuditRepository,
    DocumentProcessingRepository,
    DocumentRepository,
    DocumentVersionRepository,
)
from max.document.security.prompt_injection import DocumentSecurityEnforcer

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentService:
    """Master service facade combining document parsing, inspection, search, versioning, comparison, generation, and security."""

    def __init__(
        self,
        doc_repo: DocumentRepository,
        version_repo: DocumentVersionRepository,
        job_repo: DocumentProcessingRepository,
        audit_repo: DocumentAuditRepository,
        parser_registry: DocumentParserRegistry | None = None,
        filesystem_adapter: DocumentFilesystemAdapter | None = None,
        generator: BaseDocumentGenerator | None = None,
        converter: BaseDocumentConverter | None = None,
        security_enforcer: DocumentSecurityEnforcer | None = None,
        max_file_size_mb: float = 25.0,
    ) -> None:
        self._docs = doc_repo
        self._versions = version_repo
        self._jobs = job_repo
        self._audit = audit_repo
        self._parsers = parser_registry or DocumentParserRegistry()
        self._fs = filesystem_adapter or DocumentFilesystemAdapter()
        self._generator = generator or BaseDocumentGenerator()
        self._converter = converter or BaseDocumentConverter()
        self._security = security_enforcer or DocumentSecurityEnforcer()
        self._max_size_bytes = int(max_file_size_mb * 1024 * 1024)

    # ------------------------------------------------------------------
    # Registration & Processing
    # ------------------------------------------------------------------

    async def register_document(
        self,
        source_reference: str,
        filename: str,
        source_type: DocumentSource = DocumentSource.LOCAL_FILE,
        owner_id: str = "user_default",
    ) -> Document:
        """Discover and register a document entity."""
        raw_bytes = await self._fs.read_bytes(source_reference, owner_id=owner_id)
        if len(raw_bytes) > self._max_size_bytes:
            raise DocumentTooLargeError(
                f"Document size ({len(raw_bytes)} bytes) exceeds maximum limit ({self._max_size_bytes} bytes).",
                details={"file_size": len(raw_bytes), "max_size": self._max_size_bytes},
            )

        content_hash = hashlib.sha256(raw_bytes).hexdigest()
        existing = self._docs.get_by_hash(content_hash)
        if existing:
            return existing

        fmt = self._parsers.detect_format(filename=filename, content_bytes=raw_bytes)
        doc_type = self._map_format_to_type(fmt)

        doc = Document(
            owner_id=owner_id,
            source_type=source_type,
            source_reference=source_reference,
            filename=filename,
            normalized_filename=filename.lower().strip(),
            format=fmt,
            doc_type=doc_type,
            content_hash=content_hash,
            status=DocumentStatus.DISCOVERED,
        )

        self._docs.save(doc)
        self._audit.record(doc.id, "DOCUMENT_REGISTERED", {"filename": filename, "format": fmt.value})
        return doc

    async def process_document(self, document_id: str) -> DocumentExtractionResult:
        """Parse document, extract structure and metadata, create version 1, and wrap untrusted content."""
        doc = self._docs.get(document_id)
        job = DocumentProcessingJob(document_id=document_id, status=ProcessingStatus.PARSING, started_at=_utc_now())
        self._jobs.save(job)

        try:
            raw_bytes = await self._fs.read_bytes(doc.source_reference, owner_id=doc.owner_id)
            parser = self._parsers.resolve(fmt=doc.format, filename=doc.filename, content_bytes=raw_bytes)

            version_id = f"dver_{hashlib.md5((doc.id + str(_utc_now())).encode()).hexdigest()[:12]}"
            extraction = parser.parse(
                document_id=doc.id,
                version_id=version_id,
                content_bytes=raw_bytes,
                filename=doc.filename,
                source_reference=doc.source_reference,
            )

            # Security: inspect & wrap raw text with untrusted data boundaries
            wrapped_text, has_injection, signals = self._security.inspect_and_wrap_content(extraction.raw_text)
            if has_injection:
                extraction.warnings.append(f"Prompt injection signal detected: {', '.join(signals)}")

            doc.raw_text = wrapped_text
            doc.metadata = extraction.metadata
            doc.structure = extraction.structure
            doc.status = DocumentStatus.PROCESSED
            doc.current_version_id = version_id
            self._docs.save(doc)

            ver = DocumentVersion(
                version_id=version_id,
                document_id=doc.id,
                version_number=1,
                content_hash=doc.content_hash,
                file_size_bytes=len(raw_bytes),
                change_summary="Initial processed version",
            )
            self._versions.save(ver)

            job.status = ProcessingStatus.COMPLETED
            job.completed_at = _utc_now()
            self._jobs.save(job)

            self._audit.record(doc.id, "DOCUMENT_PROCESSED", {"version_id": version_id})
            return extraction

        except Exception as exc:
            job.status = ProcessingStatus.FAILED
            job.error = DocumentProcessingError(error_type=exc.__class__.__name__, message=str(exc))
            job.completed_at = _utc_now()
            self._jobs.save(job)

            doc.status = DocumentStatus.FAILED
            self._docs.save(doc)

            self._audit.record(doc.id, "DOCUMENT_PROCESSING_FAILED", {"error": str(exc)})
            raise

    # ------------------------------------------------------------------
    # Retrieval & Listings
    # ------------------------------------------------------------------

    def get_document(self, document_id: str) -> Document:
        return self._docs.get(document_id)

    def get_metadata(self, document_id: str) -> DocumentMetadata:
        doc = self._docs.get(document_id)
        if not doc.metadata:
            raise DocumentValidationError(f"Metadata not yet extracted for document '{document_id}'.")
        return doc.metadata

    def get_structure(self, document_id: str) -> Any:
        doc = self._docs.get(document_id)
        if not doc.structure:
            raise DocumentValidationError(f"Structure not yet extracted for document '{document_id}'.")
        return doc.structure

    def get_content(self, document_id: str) -> str:
        doc = self._docs.get(document_id)
        return doc.raw_text

    def list_documents(
        self, owner_id: str | None = None, doc_type: str | None = None, format_ext: str | None = None
    ) -> list[Document]:
        return self._docs.list_all(owner_id=owner_id, doc_type=doc_type, format_ext=format_ext)

    def list_versions(self, document_id: str) -> list[DocumentVersion]:
        return self._versions.list_for_document(document_id)

    def get_version(self, version_id: str) -> DocumentVersion:
        return self._versions.get(version_id)

    def get_summary(self, document_id: str) -> DocumentSummary:
        doc = self._docs.get(document_id)
        meta = doc.metadata
        struct = doc.structure

        sections = [s.title for s in (struct.sections if struct else []) if s.title]
        summary_txt = doc.raw_text[:300].replace("\n", " ").strip() if doc.raw_text else "No content preview"

        return DocumentSummary(
            document_id=doc.id,
            title=meta.title if meta else doc.filename,
            doc_type=doc.doc_type,
            format=doc.format,
            summary_text=summary_txt,
            key_sections=sections[:5],
            table_count=len(struct.tables) if struct else 0,
            page_count=meta.page_count if meta else 1,
            word_count=meta.word_count if meta else 0,
        )

    # ------------------------------------------------------------------
    # Search, Comparison & RAG
    # ------------------------------------------------------------------

    def search_documents(self, req: DocumentSearchRequest) -> DocumentSearchResponse:
        """Deterministic exact text search across processed documents."""
        docs = self._docs.list_all()
        if req.document_ids:
            docs = [d for d in docs if d.id in req.document_ids]
        if req.doc_types:
            docs = [d for d in docs if d.doc_type in req.doc_types]

        results: list[DocumentSearchResult] = []
        query_str = req.query if req.case_sensitive else req.query.lower()

        for doc in docs:
            text = doc.raw_text
            target_text = text if req.case_sensitive else text.lower()
            idx = 0

            while True:
                pos = target_text.find(query_str, idx)
                if pos == -1 or len(results) >= req.max_results:
                    break

                matched_segment = text[pos : pos + len(req.query)]
                start_window = max(0, pos - 40)
                end_window = min(len(text), pos + len(req.query) + 40)
                context = text[start_window:end_window].replace("\n", " ")

                citation = DocumentCitation(
                    document_id=doc.id,
                    version_id=doc.current_version_id or "v1",
                    filename=doc.filename,
                    excerpt=context,
                    formatted_citation=f"[{doc.filename}]",
                )

                results.append(
                    DocumentSearchResult(
                        document_id=doc.id,
                        filename=doc.filename,
                        matched_text=matched_segment,
                        context=context,
                        citation=citation,
                    )
                )
                idx = pos + len(query_str)

        return DocumentSearchResponse(query=req.query, total_matches=len(results), results=results)

    def compare_documents(self, source_doc_id: str, target_doc_id: str) -> DocumentComparison:
        """Compute structured machine-readable diff between two documents."""
        src_doc = self._docs.get(source_doc_id)
        tgt_doc = self._docs.get(target_doc_id)

        src_lines = src_doc.raw_text.splitlines()
        tgt_lines = tgt_doc.raw_text.splitlines()

        matcher = difflib.SequenceMatcher(None, src_lines, tgt_lines)
        changes: list[DocumentChange] = []
        added = removed = modified = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                modified += 1
                changes.append(
                    DocumentChange(
                        change_type=ComparisonChangeType.MODIFIED,
                        location=f"lines {i1+1}-{i2}",
                        old_value="\n".join(src_lines[i1:i2]),
                        new_value="\n".join(tgt_lines[j1:j2]),
                    )
                )
            elif tag == "delete":
                removed += 1
                changes.append(
                    DocumentChange(
                        change_type=ComparisonChangeType.REMOVED,
                        location=f"lines {i1+1}-{i2}",
                        old_value="\n".join(src_lines[i1:i2]),
                    )
                )
            elif tag == "insert":
                added += 1
                changes.append(
                    DocumentChange(
                        change_type=ComparisonChangeType.ADDED,
                        location=f"lines {j1+1}-{j2}",
                        new_value="\n".join(tgt_lines[j1:j2]),
                    )
                )

        comp = DocumentComparison(
            source_document_id=src_doc.id,
            target_document_id=tgt_doc.id,
            source_version_id=src_doc.current_version_id or "v1",
            target_version_id=tgt_doc.current_version_id or "v1",
            changes=changes,
            added_count=added,
            removed_count=removed,
            modified_count=modified,
            summary=f"Diff: +{added} -{removed} ~{modified}",
        )

        self._audit.record(src_doc.id, "DOCUMENTS_COMPARED", {"target_id": tgt_doc.id})
        return comp

    def prepare_rag(self, document_id: str) -> list[dict[str, Any]]:
        """Prepare document RAG chunk candidates for Module 10."""
        doc = self._docs.get(document_id)
        return DocumentRAGAdapter.prepare_rag_chunks(doc)

    # ------------------------------------------------------------------
    # Generation & Conversion
    # ------------------------------------------------------------------

    async def generate_document(
        self, req: DocumentGenerationRequest, output_dir: str
    ) -> DocumentGenerationResult:
        """Generate a new document file from request payload."""
        result = self._generator.generate(req, output_dir)

        # Automatically register generated document
        doc = Document(
            id=result.document_id,
            owner_id=req.owner_id,
            source_type=DocumentSource.LOCAL_FILE,
            source_reference=result.output_path,
            filename=result.filename,
            normalized_filename=result.filename.lower().strip(),
            format=result.format,
            doc_type=self._map_format_to_type(result.format),
            content_hash=result.content_hash,
            status=DocumentStatus.PROCESSED,
            raw_text=req.content_markdown,
        )
        self._docs.save(doc)
        self._audit.record(doc.id, "DOCUMENT_GENERATED", {"path": result.output_path})
        return result

    async def convert_document(
        self, req: DocumentConversionRequest, output_dir: str
    ) -> DocumentConversionResult:
        """Convert an existing document to a target format."""
        src_doc = self._docs.get(req.source_document_id)
        result = self._converter.convert(req, src_doc, output_dir)

        self._audit.record(
            src_doc.id, "DOCUMENT_CONVERTED", {"target_format": req.target_format.value}
        )
        return result

    def validate_document(self, document_id: str) -> DocumentValidationResult:
        """Perform validation checks on a registered document."""
        doc = self._docs.get(document_id)
        errors: list[str] = []
        warnings: list[str] = []

        if doc.status == DocumentStatus.FAILED:
            errors.append("Document processing failed.")
        if not doc.content_hash:
            errors.append("Missing content SHA-256 hash.")
        if not doc.raw_text:
            warnings.append("Document text content is empty.")

        return DocumentValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            security_verdict="PASSED" if len(errors) == 0 else "FAILED",
        )

    def delete_document(self, document_id: str) -> bool:
        """Delete document from repository."""
        success = self._docs.delete(document_id)
        if success:
            self._audit.record(document_id, "DOCUMENT_DELETED")
        return success

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_format_to_type(fmt: DocumentFormat) -> DocumentType:
        mapping = {
            DocumentFormat.PDF: DocumentType.PDF,
            DocumentFormat.DOCX: DocumentType.WORD,
            DocumentFormat.XLSX: DocumentType.SPREADSHEET,
            DocumentFormat.PPTX: DocumentType.PRESENTATION,
            DocumentFormat.TXT: DocumentType.TEXT,
            DocumentFormat.MD: DocumentType.MARKDOWN,
            DocumentFormat.CSV: DocumentType.CSV,
            DocumentFormat.JSON: DocumentType.JSON,
            DocumentFormat.XML: DocumentType.XML,
        }
        return mapping.get(fmt, DocumentType.UNKNOWN)

"""Plain text parser for Module 24 — Document Intelligence."""

import hashlib
from datetime import datetime, timezone

from max.document.domain.enums import DocumentFormat, DocumentSource, ElementType
from max.document.domain.models import (
    DocumentElement,
    DocumentExtractionResult,
    DocumentLocation,
    DocumentMetadata,
    DocumentPage,
    DocumentParagraph,
    DocumentProvenance,
    DocumentStructure,
)
from max.document.parsers.base import BaseDocumentParser


class TextDocumentParser(BaseDocumentParser):
    """Parses plain text (.txt) files."""

    @property
    def supported_formats(self) -> list[DocumentFormat]:
        return [DocumentFormat.TXT]

    def parse(
        self,
        document_id: str,
        version_id: str,
        content_bytes: bytes,
        filename: str,
        source_reference: str = "",
    ) -> DocumentExtractionResult:
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = content_bytes.decode("latin-1", errors="replace")

        lines = text.splitlines()
        paragraphs_raw = [p.strip() for p in text.split("\n\n") if p.strip()]

        paragraphs: list[DocumentParagraph] = []
        elements: list[DocumentElement] = []

        for idx, para_text in enumerate(paragraphs_raw, start=1):
            loc = DocumentLocation(page_number=1, row_index=idx)
            para = DocumentParagraph(text=para_text, location=loc)
            paragraphs.append(para)

            elem = DocumentElement(
                document_id=document_id,
                version_id=version_id,
                element_type=ElementType.PARAGRAPH,
                content=para_text,
                location=loc,
            )
            elements.append(elem)

        words = text.split()
        metadata = DocumentMetadata(
            filename=filename,
            normalized_filename=filename.lower().strip(),
            mime_type="text/plain",
            file_size_bytes=len(content_bytes),
            content_hash=content_hash,
            title=filename,
            page_count=1,
            word_count=len(words),
            character_count=len(text),
        )

        page = DocumentPage(page_number=1, text=text, element_ids=[e.element_id for e in elements])
        structure = DocumentStructure(
            pages=[page],
            paragraphs=paragraphs,
            elements=elements,
        )

        provenance = DocumentProvenance(
            document_id=document_id,
            version_id=version_id,
            source_type=DocumentSource.LOCAL_FILE,
            source_reference=source_reference or filename,
            content_hash=content_hash,
            processed_at=datetime.now(timezone.utc),
            parser_name="TextDocumentParser",
        )

        return DocumentExtractionResult(
            document_id=document_id,
            metadata=metadata,
            structure=structure,
            raw_text=text,
            provenance=provenance,
        )

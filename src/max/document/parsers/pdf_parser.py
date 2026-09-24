"""PDF parser for Module 24 — Document Intelligence."""

import hashlib
import io
import re
from datetime import UTC, datetime

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

# Attempt import pypdf or fitz
try:
    import pypdf
except ImportError:
    pypdf = None  # type: ignore[assignment]

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore[assignment]


class PdfDocumentParser(BaseDocumentParser):
    """Parses PDF (.pdf) documents using PyPDF / PyMuPDF with text stream fallback."""

    @property
    def supported_formats(self) -> list[DocumentFormat]:
        return [DocumentFormat.PDF]

    def parse(
        self,
        document_id: str,
        version_id: str,
        content_bytes: bytes,
        filename: str,
        source_reference: str = "",
    ) -> DocumentExtractionResult:
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        pages: list[DocumentPage] = []
        elements: list[DocumentElement] = []
        paragraphs: list[DocumentParagraph] = []
        full_text_parts: list[str] = []
        warnings: list[str] = []
        page_count = 0
        author = title = creator = None

        if fitz is not None:
            # 1. Try PyMuPDF / fitz
            try:
                doc = fitz.open(stream=content_bytes, filetype="pdf")
                page_count = len(doc)
                meta = doc.metadata or {}
                author = meta.get("author")
                title = meta.get("title")
                creator = meta.get("creator")

                for pno in range(page_count):
                    page = doc.load_page(pno)
                    p_text = page.get_text() or ""
                    full_text_parts.append(p_text)

                    p_elements: list[str] = []
                    lines = [ln.strip() for ln in p_text.splitlines() if ln.strip()]
                    for lno, line in enumerate(lines, start=1):
                        loc = DocumentLocation(page_number=pno + 1, row_index=lno)
                        para = DocumentParagraph(text=line, location=loc)
                        paragraphs.append(para)

                        elem = DocumentElement(
                            document_id=document_id,
                            version_id=version_id,
                            element_type=ElementType.PARAGRAPH,
                            content=line,
                            location=loc,
                        )
                        elements.append(elem)
                        p_elements.append(elem.element_id)

                    pages.append(
                        DocumentPage(page_number=pno + 1, text=p_text, element_ids=p_elements)
                    )
            except Exception as e:
                warnings.append(f"fitz parsing failed: {e}")

        elif pypdf is not None and not pages:
            # 2. Try pypdf
            try:
                reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                page_count = len(reader.pages)
                if reader.metadata:
                    author = reader.metadata.author
                    title = reader.metadata.title
                    creator = reader.metadata.creator

                for pno, page_obj in enumerate(reader.pages):
                    p_text = page_obj.extract_text() or ""
                    full_text_parts.append(p_text)

                    p_elements = []
                    lines = [ln.strip() for ln in p_text.splitlines() if ln.strip()]
                    for lno, line in enumerate(lines, start=1):
                        loc = DocumentLocation(page_number=pno + 1, row_index=lno)
                        para = DocumentParagraph(text=line, location=loc)
                        paragraphs.append(para)

                        elem = DocumentElement(
                            document_id=document_id,
                            version_id=version_id,
                            element_type=ElementType.PARAGRAPH,
                            content=line,
                            location=loc,
                        )
                        elements.append(elem)
                        p_elements.append(elem.element_id)

                    pages.append(
                        DocumentPage(page_number=pno + 1, text=p_text, element_ids=p_elements)
                    )
            except Exception as e:
                warnings.append(f"pypdf parsing failed: {e}")

        # 3. Native fallback if no library extracted pages
        if not pages:
            raw_str = content_bytes.decode("latin-1", errors="replace")
            # Basic page count estimation (/Type /Page)
            page_matches = re.findall(r"/Type\s*/Page\b", raw_str)
            page_count = max(len(page_matches), 1)

            # Extract uncompressed text streams ((...))
            text_blocks = re.findall(r"\(([^()]{3,})\)\s*Tj", raw_str)
            raw_extracted = "\n".join(text_blocks) if text_blocks else ""

            if not raw_extracted:
                warnings.append("No readable text stream found. Document may be scanned or encrypted (requires Module 25 Vision System).")

            full_text_parts.append(raw_extracted)
            elem = DocumentElement(
                document_id=document_id,
                version_id=version_id,
                element_type=ElementType.PAGE,
                content=raw_extracted or "[Scanned PDF content - visual OCR required]",
                location=DocumentLocation(page_number=1),
            )
            elements.append(elem)
            pages.append(DocumentPage(page_number=1, text=raw_extracted, element_ids=[elem.element_id]))

        raw_text = "\n\n".join(full_text_parts)
        words = raw_text.split()

        metadata = DocumentMetadata(
            filename=filename,
            normalized_filename=filename.lower().strip(),
            mime_type="application/pdf",
            file_size_bytes=len(content_bytes),
            content_hash=content_hash,
            author=author,
            creator=creator,
            title=title or filename,
            page_count=page_count,
            word_count=len(words),
            character_count=len(raw_text),
        )

        structure = DocumentStructure(
            pages=pages,
            paragraphs=paragraphs,
            elements=elements,
        )

        provenance = DocumentProvenance(
            document_id=document_id,
            version_id=version_id,
            source_type=DocumentSource.LOCAL_FILE,
            source_reference=source_reference or filename,
            content_hash=content_hash,
            processed_at=datetime.now(UTC),
            parser_name="PdfDocumentParser",
        )

        return DocumentExtractionResult(
            document_id=document_id,
            metadata=metadata,
            structure=structure,
            raw_text=raw_text,
            provenance=provenance,
            warnings=warnings,
        )

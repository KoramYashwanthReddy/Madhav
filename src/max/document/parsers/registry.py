"""Parser registry for Module 24 — Document Intelligence."""

import logging

from max.document.domain.enums import DocumentFormat
from max.document.domain.exceptions import UnsupportedDocumentFormatError
from max.document.parsers.base import BaseDocumentParser
from max.document.parsers.csv_parser import CsvDocumentParser
from max.document.parsers.docx_parser import DocxDocumentParser
from max.document.parsers.json_parser import JsonDocumentParser
from max.document.parsers.markdown_parser import MarkdownDocumentParser
from max.document.parsers.pdf_parser import PdfDocumentParser
from max.document.parsers.pptx_parser import PptxDocumentParser
from max.document.parsers.text_parser import TextDocumentParser
from max.document.parsers.xlsx_parser import XlsxDocumentParser
from max.document.parsers.xml_parser import XmlDocumentParser

logger = logging.getLogger(__name__)


class DocumentParserRegistry:
    """Central registry resolving the appropriate parser for a document."""

    def __init__(self, register_defaults: bool = True) -> None:
        self._parsers: dict[DocumentFormat, BaseDocumentParser] = {}
        if register_defaults:
            self._register_default_parsers()

    def register(self, parser: BaseDocumentParser) -> None:
        """Register a parser instance for its supported formats."""
        for fmt in parser.supported_formats:
            self._parsers[fmt] = parser
            logger.debug("Registered parser %s for format %s", parser.__class__.__name__, fmt.value)

    def resolve(
        self,
        fmt: DocumentFormat | str | None = None,
        filename: str = "",
        mime_type: str = "",
        content_bytes: bytes | None = None,
    ) -> BaseDocumentParser:
        """Resolve suitable parser using format, filename extension, MIME type, and magic bytes."""
        detected_fmt = self.detect_format(fmt=fmt, filename=filename, mime_type=mime_type, content_bytes=content_bytes)
        if detected_fmt in self._parsers:
            return self._parsers[detected_fmt]

        raise UnsupportedDocumentFormatError(
            f"No registered document parser found for format '{detected_fmt.value}'.",
            details={"detected_format": detected_fmt.value, "filename": filename, "mime_type": mime_type},
        )

    def detect_format(
        self,
        fmt: DocumentFormat | str | None = None,
        filename: str = "",
        mime_type: str = "",
        content_bytes: bytes | None = None,
    ) -> DocumentFormat:
        """Multi-signal format detection combining explicit format, extension, MIME, and magic bytes."""
        # 1. Explicit format argument
        if isinstance(fmt, DocumentFormat) and fmt != DocumentFormat.UNKNOWN:
            return fmt
        if isinstance(fmt, str) and fmt.strip():
            try:
                return DocumentFormat(fmt.strip().lower())
            except ValueError:
                pass

        # 2. Filename extension signal
        ext_map = {
            ".pdf": DocumentFormat.PDF,
            ".docx": DocumentFormat.DOCX,
            ".xlsx": DocumentFormat.XLSX,
            ".pptx": DocumentFormat.PPTX,
            ".txt": DocumentFormat.TXT,
            ".md": DocumentFormat.MD,
            ".markdown": DocumentFormat.MD,
            ".csv": DocumentFormat.CSV,
            ".json": DocumentFormat.JSON,
            ".xml": DocumentFormat.XML,
        }
        if filename:
            low_fn = filename.lower()
            for ext, f_val in ext_map.items():
                if low_fn.endswith(ext):
                    return f_val

        # 3. MIME type signal
        mime_map = {
            "application/pdf": DocumentFormat.PDF,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentFormat.DOCX,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": DocumentFormat.XLSX,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": DocumentFormat.PPTX,
            "text/plain": DocumentFormat.TXT,
            "text/markdown": DocumentFormat.MD,
            "text/csv": DocumentFormat.CSV,
            "application/json": DocumentFormat.JSON,
            "application/xml": DocumentFormat.XML,
            "text/xml": DocumentFormat.XML,
        }
        if mime_type and mime_type.lower() in mime_map:
            return mime_map[mime_type.lower()]

        # 4. Magic bytes signature signal
        if content_bytes and len(content_bytes) >= 4:
            if content_bytes.startswith(b"%PDF"):
                return DocumentFormat.PDF
            if content_bytes.startswith(b"{\n") or content_bytes.startswith(b"{\r") or content_bytes.startswith(b"{\""):
                return DocumentFormat.JSON
            if content_bytes.startswith(b"<?xml") or content_bytes.startswith(b"<"):
                return DocumentFormat.XML

        return DocumentFormat.UNKNOWN

    def _register_default_parsers(self) -> None:
        self.register(TextDocumentParser())
        self.register(MarkdownDocumentParser())
        self.register(CsvDocumentParser())
        self.register(JsonDocumentParser())
        self.register(XmlDocumentParser())
        self.register(PdfDocumentParser())
        self.register(DocxDocumentParser())
        self.register(XlsxDocumentParser())
        self.register(PptxDocumentParser())

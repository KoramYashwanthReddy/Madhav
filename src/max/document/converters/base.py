"""Document conversion subsystem for Module 24 — Document Intelligence."""

import hashlib
import json
import os

from max.document.domain.enums import DocumentFormat
from max.document.domain.exceptions import DocumentConversionError
from max.document.domain.models import (
    Document,
    DocumentConversionRequest,
    DocumentConversionResult,
)


class BaseDocumentConverter:
    """Deterministic format converter between supported document representations."""

    def convert(
        self,
        req: DocumentConversionRequest,
        source_doc: Document,
        output_dir: str,
    ) -> DocumentConversionResult:
        """Convert source document into requested target format."""
        os.makedirs(output_dir, exist_ok=True)
        filename = req.output_filename or f"converted_{source_doc.filename}.{req.target_format.value}"
        out_path = os.path.join(output_dir, filename)

        text = source_doc.raw_text or ""
        target_fmt = req.target_format
        content_bytes = b""

        if target_fmt in (DocumentFormat.TXT, DocumentFormat.MD):
            content_bytes = text.encode("utf-8")
        elif target_fmt == DocumentFormat.JSON:
            obj = {
                "document_id": source_doc.id,
                "filename": source_doc.filename,
                "content": text,
            }
            content_bytes = json.dumps(obj, indent=2).encode("utf-8")
        elif target_fmt == DocumentFormat.CSV:
            lines = text.splitlines()
            csv_parts = []
            for i, line in enumerate(lines, start=1):
                escaped = line.replace('"', '""')
                csv_parts.append(f'"line_{i}","{escaped}"')
            content_bytes = ("line_number,content\n" + "\n".join(csv_parts)).encode("utf-8")
        elif target_fmt in (DocumentFormat.PDF, DocumentFormat.DOCX, DocumentFormat.XLSX, DocumentFormat.PPTX, DocumentFormat.XML):
            content_bytes = f"<!-- CONVERTED TO {target_fmt.value.upper()} -->\n{text}".encode()
        else:
            raise DocumentConversionError(
                f"Unsupported target format for conversion: '{target_fmt.value}'",
                details={"target_format": target_fmt.value},
            )

        with open(out_path, "wb") as f:
            f.write(content_bytes)

        content_hash = hashlib.sha256(content_bytes).hexdigest()
        conv_doc_id = f"doc_conv_{hashlib.md5(out_path.encode()).hexdigest()[:10]}"

        return DocumentConversionResult(
            source_document_id=source_doc.id,
            target_document_id=conv_doc_id,
            target_format=target_fmt,
            output_path=out_path,
            content_hash=content_hash,
        )

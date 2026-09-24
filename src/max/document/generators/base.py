"""Document generation subsystem for Module 24 — Document Intelligence."""

import hashlib
import json
import os
from datetime import datetime, timezone

from max.document.domain.enums import DocumentFormat
from max.document.domain.exceptions import DocumentGenerationError
from max.document.domain.models import DocumentGenerationRequest, DocumentGenerationResult


class BaseDocumentGenerator:
    """Provider-neutral document generator producing formatted files from Markdown/data."""

    def generate(self, req: DocumentGenerationRequest, target_dir: str) -> DocumentGenerationResult:
        """Generate document into target directory and return metadata result."""
        os.makedirs(target_dir, exist_ok=True)
        out_path = os.path.join(target_dir, req.filename)

        # Prevent silent overwrite
        if os.path.exists(out_path):
            raise DocumentGenerationError(
                f"Generation target file '{out_path}' already exists.",
                details={"path": out_path},
            )

        fmt = req.target_format
        content_bytes = b""

        if fmt in (DocumentFormat.TXT, DocumentFormat.MD):
            content_bytes = req.content_markdown.encode("utf-8")
        elif fmt == DocumentFormat.JSON:
            doc_obj = {"title": req.title, "content": req.content_markdown}
            if req.tables:
                doc_obj["tables"] = [t.model_dump() for t in req.tables]
            content_bytes = json.dumps(doc_obj, indent=2).encode("utf-8")
        elif fmt == DocumentFormat.CSV:
            csv_lines: list[str] = [f"# {req.title}", f"# Content: {req.content_markdown}"]
            if req.tables and req.tables[0].rows:
                tbl = req.tables[0]
                csv_lines.append(",".join(tbl.headers))
                for r in tbl.rows:
                    csv_lines.append(",".join(c.content for c in r.cells))
            content_bytes = "\n".join(csv_lines).encode("utf-8")
        elif fmt in (DocumentFormat.PDF, DocumentFormat.DOCX, DocumentFormat.XLSX, DocumentFormat.PPTX, DocumentFormat.XML):
            # Formatted text / XML structural fallback representation
            header = f"<!-- GENERATED {fmt.value.upper()} DOCUMENT: {req.title} -->\n"
            content_bytes = (header + req.content_markdown).encode("utf-8")
        else:
            raise DocumentGenerationError(
                f"Document generation for format '{fmt.value}' is not supported.",
                details={"format": fmt.value},
            )

        with open(out_path, "wb") as f:
            f.write(content_bytes)

        content_hash = hashlib.sha256(content_bytes).hexdigest()
        doc_id = f"doc_gen_{hashlib.md5(out_path.encode()).hexdigest()[:10]}"

        return DocumentGenerationResult(
            document_id=doc_id,
            filename=req.filename,
            output_path=out_path,
            format=fmt,
            content_hash=content_hash,
            file_size_bytes=len(content_bytes),
        )

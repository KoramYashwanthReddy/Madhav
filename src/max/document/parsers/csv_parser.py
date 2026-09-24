"""CSV document parser for Module 24 — Document Intelligence."""

import csv
import hashlib
import io
from datetime import datetime, timezone

from max.document.domain.enums import DocumentFormat, DocumentSource, ElementType
from max.document.domain.models import (
    DocumentElement,
    DocumentExtractionResult,
    DocumentLocation,
    DocumentMetadata,
    DocumentPage,
    DocumentProvenance,
    DocumentStructure,
    DocumentTable,
    DocumentTableCell,
    DocumentTableRow,
)
from max.document.parsers.base import BaseDocumentParser


class CsvDocumentParser(BaseDocumentParser):
    """Parses CSV (.csv) documents into structured tables."""

    @property
    def supported_formats(self) -> list[DocumentFormat]:
        return [DocumentFormat.CSV]

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

        # Sniff delimiter
        delimiter = ","
        try:
            dialect = csv.Sniffer().sniff(text[:2048], delimiters=",;\t|")
            delimiter = dialect.delimiter
        except Exception:
            pass

        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        raw_rows = list(reader)

        headers: list[str] = []
        data_rows: list[list[str]] = []

        if raw_rows:
            headers = [str(cell).strip() for cell in raw_rows[0]]
            data_rows = raw_rows[1:]

        table_rows: list[DocumentTableRow] = []
        for row_idx, r_cells in enumerate(data_rows):
            cells = [
                DocumentTableCell(row_index=row_idx, column_index=col_idx, content=str(cell).strip())
                for col_idx, cell in enumerate(r_cells)
            ]
            table_rows.append(DocumentTableRow(row_index=row_idx, cells=cells))

        table = DocumentTable(
            headers=headers,
            rows=table_rows,
            row_count=len(table_rows),
            column_count=len(headers) if headers else (len(raw_rows[0]) if raw_rows else 0),
            location=DocumentLocation(page_number=1, row_index=0),
        )

        elements: list[DocumentElement] = [
            DocumentElement(
                document_id=document_id,
                version_id=version_id,
                element_type=ElementType.TABLE,
                content=f"CSV Table ({len(table_rows)} rows x {len(headers)} cols)",
                location=DocumentLocation(page_number=1, row_index=0),
                metadata={
                    "delimiter": delimiter,
                    "row_count": len(table_rows),
                    "column_count": len(headers),
                },
            )
        ]

        metadata = DocumentMetadata(
            filename=filename,
            normalized_filename=filename.lower().strip(),
            mime_type="text/csv",
            file_size_bytes=len(content_bytes),
            content_hash=content_hash,
            title=filename,
            page_count=1,
            word_count=sum(len(" ".join(row).split()) for row in raw_rows),
            character_count=len(text),
            custom_properties={"delimiter": delimiter, "row_count": len(raw_rows)},
        )

        page = DocumentPage(page_number=1, text=text, element_ids=[e.element_id for e in elements])
        structure = DocumentStructure(
            pages=[page],
            tables=[table],
            elements=elements,
        )

        provenance = DocumentProvenance(
            document_id=document_id,
            version_id=version_id,
            source_type=DocumentSource.LOCAL_FILE,
            source_reference=source_reference or filename,
            content_hash=content_hash,
            processed_at=datetime.now(timezone.utc),
            parser_name="CsvDocumentParser",
        )

        return DocumentExtractionResult(
            document_id=document_id,
            metadata=metadata,
            structure=structure,
            raw_text=text,
            provenance=provenance,
        )

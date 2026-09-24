"""JSON document parser for Module 24 — Document Intelligence."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

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


class JsonDocumentParser(BaseDocumentParser):
    """Parses JSON (.json) documents into structural elements and key-path mappings."""

    @property
    def supported_formats(self) -> list[DocumentFormat]:
        return [DocumentFormat.JSON]

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

        data = json.loads(text)
        elements: list[DocumentElement] = []
        tables: list[DocumentTable] = []

        self._flatten_json(data, "root", document_id, version_id, elements)

        # Check if root or child is a tabular list of dicts
        if isinstance(data, list) and data and all(isinstance(x, dict) for x in data):
            tbl = self._dict_list_to_table(data)
            if tbl:
                tables.append(tbl)

        words = text.split()
        metadata = DocumentMetadata(
            filename=filename,
            normalized_filename=filename.lower().strip(),
            mime_type="application/json",
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
            tables=tables,
            elements=elements,
        )

        provenance = DocumentProvenance(
            document_id=document_id,
            version_id=version_id,
            source_type=DocumentSource.LOCAL_FILE,
            source_reference=source_reference or filename,
            content_hash=content_hash,
            processed_at=datetime.now(UTC),
            parser_name="JsonDocumentParser",
        )

        return DocumentExtractionResult(
            document_id=document_id,
            metadata=metadata,
            structure=structure,
            raw_text=text,
            provenance=provenance,
        )

    def _flatten_json(
        self,
        obj: Any,
        path: str,
        document_id: str,
        version_id: str,
        elements: list[DocumentElement],
    ) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}"
                self._flatten_json(v, new_path, document_id, version_id, elements)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                new_path = f"{path}[{idx}]"
                self._flatten_json(item, new_path, document_id, version_id, elements)
        else:
            elem = DocumentElement(
                document_id=document_id,
                version_id=version_id,
                element_type=ElementType.CUSTOM,
                content=f"{path} = {obj}",
                location=DocumentLocation(page_number=1),
                metadata={"key_path": path, "value": str(obj)},
            )
            elements.append(elem)

    def _dict_list_to_table(self, data: list[dict[str, Any]]) -> DocumentTable | None:
        if not data:
            return None
        headers = list(data[0].keys())
        rows: list[DocumentTableRow] = []
        for r_idx, d in enumerate(data):
            cells = [
                DocumentTableCell(row_index=r_idx, column_index=c_idx, content=str(d.get(h, "")))
                for c_idx, h in enumerate(headers)
            ]
            rows.append(DocumentTableRow(row_index=r_idx, cells=cells))
        return DocumentTable(
            headers=headers,
            rows=rows,
            row_count=len(rows),
            column_count=len(headers),
            location=DocumentLocation(page_number=1),
        )

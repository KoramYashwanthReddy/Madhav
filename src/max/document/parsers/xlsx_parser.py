"""XLSX document parser for Module 24 — Document Intelligence."""

import hashlib
import io
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime

from max.document.domain.enums import DocumentFormat, DocumentSource, ElementType
from max.document.domain.models import (
    DocumentElement,
    DocumentExtractionResult,
    DocumentLocation,
    DocumentMetadata,
    DocumentPage,
    DocumentProvenance,
    DocumentSheet,
    DocumentStructure,
    DocumentTable,
    DocumentTableCell,
    DocumentTableRow,
)
from max.document.parsers.base import BaseDocumentParser

try:
    import openpyxl
except ImportError:
    openpyxl = None


class XlsxDocumentParser(BaseDocumentParser):
    """Parses Excel (.xlsx) documents into sheets, rows, and tables. Formula values are read without executing macros."""

    @property
    def supported_formats(self) -> list[DocumentFormat]:
        return [DocumentFormat.XLSX]

    def parse(
        self,
        document_id: str,
        version_id: str,
        content_bytes: bytes,
        filename: str,
        source_reference: str = "",
    ) -> DocumentExtractionResult:
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        sheets: list[DocumentSheet] = []
        tables: list[DocumentTable] = []
        elements: list[DocumentElement] = []
        full_text_parts: list[str] = []

        if openpyxl is not None:
            # 1. Try openpyxl
            try:
                wb = openpyxl.load_workbook(io.BytesIO(content_bytes), data_only=True, read_only=True)
                for sheet_idx, sheet_name in enumerate(wb.sheetnames):
                    ws = wb[sheet_name]
                    raw_rows: list[list[str]] = []

                    for row in ws.iter_rows(values_only=True):
                        row_vals = [str(cell).strip() if cell is not None else "" for cell in row]
                        if any(row_vals):
                            raw_rows.append(row_vals)

                    if not raw_rows:
                        continue

                    headers = raw_rows[0]
                    t_rows: list[DocumentTableRow] = []
                    for r_idx, r_cells in enumerate(raw_rows[1:]):
                        cells = [
                            DocumentTableCell(row_index=r_idx, column_index=c_idx, content=cell)
                            for c_idx, cell in enumerate(r_cells)
                        ]
                        t_rows.append(DocumentTableRow(row_index=r_idx, cells=cells))

                    tbl = DocumentTable(
                        caption=sheet_name,
                        headers=headers,
                        rows=t_rows,
                        row_count=len(t_rows),
                        column_count=len(headers),
                        location=DocumentLocation(page_number=1, sheet_name=sheet_name),
                    )
                    tables.append(tbl)

                    sheet_obj = DocumentSheet(
                        sheet_name=sheet_name,
                        sheet_index=sheet_idx,
                        tables=[tbl],
                        row_count=len(raw_rows),
                        column_count=len(headers),
                        text_preview=f"Sheet {sheet_name}: {len(raw_rows)} rows",
                    )
                    sheets.append(sheet_obj)

                    elem = DocumentElement(
                        document_id=document_id,
                        version_id=version_id,
                        element_type=ElementType.SHEET,
                        content=f"Sheet '{sheet_name}' ({len(raw_rows)} rows x {len(headers)} cols)",
                        location=DocumentLocation(page_number=1, sheet_name=sheet_name),
                        metadata={"sheet_name": sheet_name, "rows": len(raw_rows)},
                    )
                    elements.append(elem)

                    sheet_text = "\n".join(" | ".join(r) for r in raw_rows)
                    full_text_parts.append(f"--- Sheet: {sheet_name} ---\n{sheet_text}")
            except Exception:
                pass

        # 2. Zip XML fallback if openpyxl not available
        if not sheets:
            try:
                with zipfile.ZipFile(io.BytesIO(content_bytes)) as z:
                    shared_strings: list[str] = []
                    if "xl/sharedStrings.xml" in z.namelist():
                        ss_data = z.read("xl/sharedStrings.xml")
                        ss_root = ET.fromstring(ss_data)
                        ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                        for si in ss_root.findall(".//ns:t", ns):
                            shared_strings.append(si.text or "")

                    sheet_files = [f for f in z.namelist() if f.startswith("xl/worksheets/sheet")]
                    for idx, sfile in enumerate(sheet_files):
                        s_data = z.read(sfile)
                        s_root = ET.fromstring(s_data)
                        ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                        s_name = f"Sheet{idx+1}"

                        row_texts: list[str] = []
                        for row in s_root.findall(".//ns:row", ns):
                            cells_vals: list[str] = []
                            for c in row.findall("ns:c", ns):
                                val_elem = c.find("ns:v", ns)
                                val = (val_elem.text if val_elem is not None else "") or ""
                                if c.attrib.get("t") == "s" and val.isdigit():
                                    val_idx = int(val)
                                    val = shared_strings[val_idx] if val_idx < len(shared_strings) else val
                                cells_vals.append(val)
                            if any(cells_vals):
                                row_texts.append(" | ".join(cells_vals))

                        if row_texts:
                            s_text = "\n".join(row_texts)
                            full_text_parts.append(f"--- Sheet: {s_name} ---\n{s_text}")
                            elem = DocumentElement(
                                document_id=document_id,
                                version_id=version_id,
                                element_type=ElementType.SHEET,
                                content=s_text[:200],
                                location=DocumentLocation(page_number=1, sheet_name=s_name),
                            )
                            elements.append(elem)
                            sheets.append(
                                DocumentSheet(
                                    sheet_name=s_name,
                                    sheet_index=idx,
                                    text_preview=s_text[:200],
                                )
                            )
            except Exception:
                pass

        raw_text = "\n\n".join(full_text_parts)
        words = raw_text.split()

        metadata = DocumentMetadata(
            filename=filename,
            normalized_filename=filename.lower().strip(),
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            file_size_bytes=len(content_bytes),
            content_hash=content_hash,
            title=filename,
            page_count=1,
            sheet_count=len(sheets),
            word_count=len(words),
            character_count=len(raw_text),
        )

        page = DocumentPage(page_number=1, text=raw_text, element_ids=[e.element_id for e in elements])
        structure = DocumentStructure(
            pages=[page],
            sheets=sheets,
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
            parser_name="XlsxDocumentParser",
        )

        return DocumentExtractionResult(
            document_id=document_id,
            metadata=metadata,
            structure=structure,
            raw_text=raw_text,
            provenance=provenance,
        )

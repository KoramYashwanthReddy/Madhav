"""Markdown parser for Module 24 — Document Intelligence."""

import hashlib
import re
from datetime import datetime, timezone

from max.document.domain.enums import DocumentFormat, DocumentSource, ElementType
from max.document.domain.models import (
    DocumentElement,
    DocumentExtractionResult,
    DocumentHeading,
    DocumentList,
    DocumentLocation,
    DocumentMetadata,
    DocumentPage,
    DocumentParagraph,
    DocumentProvenance,
    DocumentSection,
    DocumentStructure,
    DocumentTable,
    DocumentTableCell,
    DocumentTableRow,
)
from max.document.parsers.base import BaseDocumentParser


class MarkdownDocumentParser(BaseDocumentParser):
    """Parses Markdown (.md) documents into structured headings, paragraphs, lists, and tables."""

    @property
    def supported_formats(self) -> list[DocumentFormat]:
        return [DocumentFormat.MD]

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

        headings: list[DocumentHeading] = []
        sections: list[DocumentSection] = []
        paragraphs: list[DocumentParagraph] = []
        lists: list[DocumentList] = []
        tables: list[DocumentTable] = []
        elements: list[DocumentElement] = []

        lines = text.splitlines()
        line_idx = 0
        current_section: DocumentSection | None = None

        while line_idx < len(lines):
            line = lines[line_idx].rstrip()
            stripped = line.strip()

            if not stripped:
                line_idx += 1
                continue

            # Heading (#, ##, ###)
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                loc = DocumentLocation(page_number=1, row_index=line_idx)
                hdg = DocumentHeading(text=title, level=level, location=loc)
                headings.append(hdg)

                sec = DocumentSection(title=title, level=level, content="")
                sections.append(sec)
                current_section = sec

                elem = DocumentElement(
                    document_id=document_id,
                    version_id=version_id,
                    element_type=ElementType.HEADING,
                    content=title,
                    location=loc,
                    metadata={"level": level},
                )
                elements.append(elem)
                line_idx += 1
                continue

            # Table (| col1 | col2 |)
            if stripped.startswith("|") and stripped.endswith("|"):
                table_lines: list[str] = []
                while line_idx < len(lines) and lines[line_idx].strip().startswith("|"):
                    table_lines.append(lines[line_idx].strip())
                    line_idx += 1

                tbl = self._parse_markdown_table(table_lines, line_idx)
                if tbl:
                    tables.append(tbl)
                    elem = DocumentElement(
                        document_id=document_id,
                        version_id=version_id,
                        element_type=ElementType.TABLE,
                        content=f"Table ({tbl.row_count}x{tbl.column_count})",
                        location=DocumentLocation(page_number=1, row_index=line_idx),
                        metadata={"rows": tbl.row_count, "columns": tbl.column_count},
                    )
                    elements.append(elem)
                continue

            # List (- item, * item, 1. item)
            if re.match(r"^(\*|-|\+|\d+\.)\s+", stripped):
                list_items: list[str] = []
                is_ordered = bool(re.match(r"^\d+\.", stripped))
                while line_idx < len(lines) and re.match(r"^(\*|-|\+|\d+\.)\s+", lines[line_idx].strip()):
                    item_text = re.sub(r"^(\*|-|\+|\d+\.)\s+", "", lines[line_idx].strip())
                    list_items.append(item_text)
                    line_idx += 1

                lst = DocumentList(items=list_items, ordered=is_ordered)
                lists.append(lst)
                elem = DocumentElement(
                    document_id=document_id,
                    version_id=version_id,
                    element_type=ElementType.LIST,
                    content="\n".join(list_items),
                    location=DocumentLocation(page_number=1, row_index=line_idx),
                    metadata={"ordered": is_ordered, "item_count": len(list_items)},
                )
                elements.append(elem)
                continue

            # Code Block (``` ... ```)
            if stripped.startswith("```"):
                code_lines: list[str] = []
                line_idx += 1
                while line_idx < len(lines) and not lines[line_idx].strip().startswith("```"):
                    code_lines.append(lines[line_idx])
                    line_idx += 1
                if line_idx < len(lines):
                    line_idx += 1  # closing ```

                code_text = "\n".join(code_lines)
                elem = DocumentElement(
                    document_id=document_id,
                    version_id=version_id,
                    element_type=ElementType.CODE_BLOCK,
                    content=code_text,
                    location=DocumentLocation(page_number=1, row_index=line_idx),
                )
                elements.append(elem)
                continue

            # Regular Paragraph
            para_lines: list[str] = []
            while (
                line_idx < len(lines)
                and lines[line_idx].strip()
                and not lines[line_idx].strip().startswith("#")
                and not lines[line_idx].strip().startswith("|")
                and not re.match(r"^(\*|-|\+|\d+\.)\s+", lines[line_idx].strip())
                and not lines[line_idx].strip().startswith("```")
            ):
                para_lines.append(lines[line_idx].strip())
                line_idx += 1

            para_text = " ".join(para_lines)
            if para_text:
                loc = DocumentLocation(page_number=1, row_index=line_idx)
                para = DocumentParagraph(text=para_text, location=loc)
                paragraphs.append(para)
                if current_section:
                    current_section.content += para_text + "\n"

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
            mime_type="text/markdown",
            file_size_bytes=len(content_bytes),
            content_hash=content_hash,
            title=headings[0].text if headings else filename,
            page_count=1,
            word_count=len(words),
            character_count=len(text),
        )

        page = DocumentPage(page_number=1, text=text, element_ids=[e.element_id for e in elements])
        structure = DocumentStructure(
            pages=[page],
            sections=sections,
            headings=headings,
            paragraphs=paragraphs,
            lists=lists,
            tables=tables,
            elements=elements,
        )

        provenance = DocumentProvenance(
            document_id=document_id,
            version_id=version_id,
            source_type=DocumentSource.LOCAL_FILE,
            source_reference=source_reference or filename,
            content_hash=content_hash,
            processed_at=datetime.now(timezone.utc),
            parser_name="MarkdownDocumentParser",
        )

        return DocumentExtractionResult(
            document_id=document_id,
            metadata=metadata,
            structure=structure,
            raw_text=text,
            provenance=provenance,
        )

    def _parse_markdown_table(self, table_lines: list[str], row_offset: int) -> DocumentTable | None:
        if len(table_lines) < 2:
            return None

        # Clean borders
        parsed_rows: list[list[str]] = []
        for line in table_lines:
            cells = [c.strip() for c in line.strip("|").split("|")]
            parsed_rows.append(cells)

        if not parsed_rows:
            return None

        headers = parsed_rows[0]
        # Ignore separator row (|---|---|)
        data_rows = [r for r in parsed_rows[1:] if not all(re.match(r"^:?-+:?$", c) for c in r if c)]

        rows: list[DocumentTableRow] = []
        for idx, r_cells in enumerate(data_rows):
            row_cells = [
                DocumentTableCell(row_index=idx, column_index=col_idx, content=cell)
                for col_idx, cell in enumerate(r_cells)
            ]
            rows.append(DocumentTableRow(row_index=idx, cells=row_cells))

        return DocumentTable(
            headers=headers,
            rows=rows,
            row_count=len(rows),
            column_count=len(headers),
            location=DocumentLocation(page_number=1, row_index=row_offset),
        )

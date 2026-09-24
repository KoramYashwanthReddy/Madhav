"""Secure XML document parser for Module 24 — Document Intelligence."""

import hashlib
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from max.document.domain.enums import DocumentFormat, DocumentSource, ElementType
from max.document.domain.exceptions import DocumentSecurityError
from max.document.domain.models import (
    DocumentElement,
    DocumentExtractionResult,
    DocumentLocation,
    DocumentMetadata,
    DocumentPage,
    DocumentProvenance,
    DocumentSection,
    DocumentStructure,
)
from max.document.parsers.base import BaseDocumentParser

# Attempt import of defusedxml for XXE protection
try:
    import defusedxml.ElementTree as DefusedET
except ImportError:
    DefusedET = None


class XmlDocumentParser(BaseDocumentParser):
    """Securely parses XML (.xml) documents with XXE & entity expansion defenses."""

    @property
    def supported_formats(self) -> list[DocumentFormat]:
        return [DocumentFormat.XML]

    def parse(
        self,
        document_id: str,
        version_id: str,
        content_bytes: bytes,
        filename: str,
        source_reference: str = "",
    ) -> DocumentExtractionResult:
        content_hash = hashlib.sha256(content_bytes).hexdigest()

        # Check for XXE or entity expansion hazards in raw bytes
        raw_str = content_bytes.decode("utf-8", errors="replace")
        if "<!ENTITY" in raw_str or "<!DOCTYPE" in raw_str and "SYSTEM" in raw_str:
            raise DocumentSecurityError(
                "XML content contains DTD/external entity declarations (XXE hazard rejected).",
                details={"filename": filename},
            )

        try:
            if DefusedET is not None:
                root = DefusedET.fromstring(content_bytes)
            else:
                # Safe parser fallback
                parser = ET.XMLParser()
                root = ET.fromstring(content_bytes, parser=parser)
        except Exception as e:
            raise DocumentSecurityError(
                f"Failed to parse XML safely: {e}",
                details={"filename": filename, "error": str(e)},
            ) from e

        elements: list[DocumentElement] = []
        sections: list[DocumentSection] = []

        self._walk_xml(root, "root", document_id, version_id, elements, sections)

        raw_text = ET.tostring(root, encoding="unicode", method="text")
        words = raw_text.split()

        metadata = DocumentMetadata(
            filename=filename,
            normalized_filename=filename.lower().strip(),
            mime_type="application/xml",
            file_size_bytes=len(content_bytes),
            content_hash=content_hash,
            title=root.tag,
            page_count=1,
            word_count=len(words),
            character_count=len(raw_text),
            custom_properties={"root_tag": root.tag},
        )

        page = DocumentPage(page_number=1, text=raw_text, element_ids=[e.element_id for e in elements])
        structure = DocumentStructure(
            pages=[page],
            sections=sections,
            elements=elements,
        )

        provenance = DocumentProvenance(
            document_id=document_id,
            version_id=version_id,
            source_type=DocumentSource.LOCAL_FILE,
            source_reference=source_reference or filename,
            content_hash=content_hash,
            processed_at=datetime.now(UTC),
            parser_name="XmlDocumentParser",
        )

        return DocumentExtractionResult(
            document_id=document_id,
            metadata=metadata,
            structure=structure,
            raw_text=raw_text,
            provenance=provenance,
        )

    def _walk_xml(
        self,
        elem: ET.Element,
        path: str,
        document_id: str,
        version_id: str,
        elements: list[DocumentElement],
        sections: list[DocumentSection],
    ) -> None:
        tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        current_path = f"{path}/{tag_name}"

        elem_text = (elem.text or "").strip()
        if elem_text:
            doc_elem = DocumentElement(
                document_id=document_id,
                version_id=version_id,
                element_type=ElementType.CUSTOM,
                content=f"<{tag_name}> {elem_text}",
                location=DocumentLocation(page_number=1),
                metadata={"xml_path": current_path, "attributes": dict(elem.attrib)},
            )
            elements.append(doc_elem)

        if len(elem) > 0:
            sec = DocumentSection(title=tag_name, level=path.count("/") + 1, content=elem_text)
            sections.append(sec)
            for child in elem:
                self._walk_xml(child, current_path, document_id, version_id, elements, sections)

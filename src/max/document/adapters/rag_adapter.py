"""RAG adapter for Module 24 — Document Intelligence."""

import logging
from typing import Any

from max.document.domain.models import Document, DocumentCitation, DocumentLocation

logger = logging.getLogger(__name__)


class DocumentRAGAdapter:
    """Converts extracted document elements into RAG-ready chunk candidate records for Module 10."""

    @staticmethod
    def prepare_rag_chunks(doc: Document, max_chunk_size: int = 1000) -> list[dict[str, Any]]:
        """Extract structured chunk candidates from document for Module 10 RAG indexing."""
        chunks: list[dict[str, Any]] = []

        if not doc.structure:
            if doc.raw_text:
                chunks.append(
                    {
                        "chunk_id": f"{doc.id}_raw_0",
                        "document_id": doc.id,
                        "version_id": doc.current_version_id or "v1",
                        "content": doc.raw_text[:max_chunk_size],
                        "metadata": {
                            "filename": doc.filename,
                            "doc_type": doc.doc_type.value,
                            "format": doc.format.value,
                            "owner_id": doc.owner_id,
                        },
                        "citation": DocumentCitation(
                            document_id=doc.id,
                            version_id=doc.current_version_id or "v1",
                            filename=doc.filename,
                            excerpt=doc.raw_text[:200],
                            formatted_citation=f"[{doc.filename}]",
                        ).model_dump(),
                    }
                )
            return chunks

        # Convert sections / elements into chunks
        for idx, elem in enumerate(doc.structure.elements):
            if not elem.content.strip():
                continue

            loc = elem.location or DocumentLocation()
            loc_str = f"Page {loc.page_number}" if loc.page_number else "Document"
            if loc.sheet_name:
                loc_str += f", Sheet: {loc.sheet_name}"
            if loc.slide_number:
                loc_str += f", Slide: {loc.slide_number}"

            citation = DocumentCitation(
                document_id=doc.id,
                version_id=doc.current_version_id or "v1",
                element_id=elem.element_id,
                filename=doc.filename,
                location=loc,
                excerpt=elem.content[:200],
                formatted_citation=f"[{doc.filename}, {loc_str}]",
            )

            chunks.append(
                {
                    "chunk_id": f"{doc.id}_elem_{idx}",
                    "document_id": doc.id,
                    "version_id": doc.current_version_id or "v1",
                    "element_id": elem.element_id,
                    "content": elem.content[:max_chunk_size],
                    "metadata": {
                        "filename": doc.filename,
                        "doc_type": doc.doc_type.value,
                        "format": doc.format.value,
                        "element_type": elem.element_type.value,
                        "owner_id": doc.owner_id,
                        "location_str": loc_str,
                    },
                    "citation": citation.model_dump(),
                }
            )

        return chunks

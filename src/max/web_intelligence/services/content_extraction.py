"""ContentExtractionService for parsing, sectioning, and bounding web document text."""

import re

from max.web_intelligence.domain.models import ContentSection, WebContent, WebDocument


class ContentExtractionService:
    """Parses raw webpage text into structured sections while applying content size limits."""

    def __init__(self, max_content_bytes: int = 1048576) -> None:
        self.max_content_bytes = max_content_bytes

    def extract_and_section_content(self, document: WebDocument) -> WebContent:
        """Process document content into clean, structured sections."""
        raw_text = document.content.raw_text

        # Enforce maximum text length boundary
        if len(raw_text.encode("utf-8")) > self.max_content_bytes:
            raw_text = raw_text[: self.max_content_bytes]

        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
        sections: list[ContentSection] = []
        headings: list[str] = []

        section_idx = 0
        current_heading: str | None = None
        buffer_lines: list[str] = []

        for p in paragraphs:
            # Check if line looks like a heading
            if len(p) < 80 and not p.endswith(".") and (p.isupper() or p.istitle() or p.startswith("#")):
                if buffer_lines:
                    sections.append(
                        ContentSection(
                            heading=current_heading,
                            text="\n".join(buffer_lines),
                            section_index=section_idx,
                        )
                    )
                    section_idx += 1
                    buffer_lines.clear()

                current_heading = p.lstrip("#").strip()
                headings.append(current_heading)
            else:
                buffer_lines.append(p)

        if buffer_lines:
            sections.append(
                ContentSection(
                    heading=current_heading,
                    text="\n".join(buffer_lines),
                    section_index=section_idx,
                )
            )

        updated_content = WebContent(
            raw_text=raw_text,
            sections=sections,
            headings=headings,
            links=document.content.links,
            word_count=len(raw_text.split()),
            trust_level=document.content.trust_level,
        )

        document.content = updated_content
        return updated_content

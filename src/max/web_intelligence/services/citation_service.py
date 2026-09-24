"""CitationService for formatting and validating first-class web citations."""

from max.web_intelligence.domain.enums import CitationStyle
from max.web_intelligence.domain.exceptions import CitationValidationError
from max.web_intelligence.domain.models import Citation, Source


class CitationService:
    """Generates formatted citations and verifies citation integrity against retrieved sources."""

    def format_citation(self, source: Source, style: CitationStyle = CitationStyle.APA) -> Citation:
        """Render a formatted Citation string from source metadata."""
        meta = source.metadata
        publisher = meta.publisher or meta.domain
        pub_date = meta.published_date or "n.d."
        title = meta.title or "Untitled Web Page"
        url = meta.url
        author = meta.author or publisher

        if style == CitationStyle.APA:
            formatted = f"{author}. ({pub_date}). {title}. Retrieved from {url}"
        elif style == CitationStyle.MLA:
            formatted = f'"{title}." {publisher}, {pub_date}, {url}.'
        elif style == CitationStyle.CHICAGO:
            formatted = f'{author}. "{title}." {publisher}. {pub_date}. {url}.'
        elif style == CitationStyle.IEEE:
            formatted = f'[1] {author}, "{title}," {publisher}, {pub_date}. [Online]. Available: {url}'
        else:  # SIMPLE
            formatted = f"{title} - {url} ({pub_date})"

        return Citation(
            research_id=source.research_id,
            source_id=source.id,
            url=url,
            title=title,
            publisher=publisher,
            author=author,
            published_date=meta.published_date,
            formatted_text=formatted,
            style=style,
            is_validated=True,
        )

    def validate_citation(self, citation: Citation, valid_sources: list[Source]) -> bool:
        """Verify that citation URL maps to a genuinely retrieved source."""
        valid_urls = {s.metadata.url.rstrip("/") for s in valid_sources}
        if citation.url.rstrip("/") not in valid_urls:
            citation.is_validated = False
            raise CitationValidationError(
                citation.id,
                f"Citation URL '{citation.url}' does not correspond to any retrieved web source.",
            )
        citation.is_validated = True
        return True

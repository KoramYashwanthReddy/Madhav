"""Context Builder for converting RetrievalResults to Module 06 ContextItems."""

from typing import Any

from madhav.context.domain.enums import ContextCategory, ContextPriority, SourceTrustLevel
from madhav.context.domain.item import ContextItem
from madhav.rag.domain.result import RetrievalResult


class RetrievalContextBuilder:
    """Transforms retrieval search results into Module 06 ContextItem instances."""

    def __init__(
        self,
        default_priority: ContextPriority = ContextPriority.HIGH,
        max_characters: int = 16384,
        max_items: int = 10,
    ) -> None:
        self.default_priority = default_priority
        self.max_characters = max_characters
        self.max_items = max_items

    def build_context_items(
        self,
        results: list[RetrievalResult],
        max_characters: int | None = None,
        max_items: int | None = None,
    ) -> list[ContextItem]:
        """Convert a list of RetrievalResult objects into budget-aware ContextItems."""
        char_budget = max_characters or self.max_characters
        item_limit = max_items or self.max_items

        context_items: list[ContextItem] = []
        seen_chunk_ids: set[str] = set()
        seen_text_hashes: set[str] = set()
        accumulated_chars = 0

        for res in results:
            if len(context_items) >= item_limit:
                break

            # Deduplication by chunk_id
            if res.chunk_id in seen_chunk_ids:
                continue

            # Deduplication by text content
            text_key = res.text.strip().lower()
            if text_key in seen_text_hashes:
                continue

            # Format source label
            label = f"[Source: {res.citation.title} | Relevancy: {res.score:.2f}]"
            formatted_content = f"{label}\n{res.text}"

            content_len = len(formatted_content)

            # Check character budget
            if accumulated_chars + content_len > char_budget and context_items:
                # Truncate content if necessary
                allowed_len = char_budget - accumulated_chars - len(label) - 10
                if allowed_len > 50:
                    truncated_text = res.text[:allowed_len] + "..."
                    formatted_content = f"{label}\n{truncated_text}"
                    content_len = len(formatted_content)
                else:
                    break

            token_est = max(1, content_len // 4)

            item_metadata: dict[str, Any] = {
                "chunk_id": res.chunk_id,
                "document_id": res.document_id,
                "score": res.score,
                "rank": res.rank,
                "source_type": str(res.source.source_type),
                "source_reference": res.source.source_reference,
                "citation": res.citation.model_dump(),
            }

            item = ContextItem(
                category=ContextCategory.KNOWLEDGE,
                content=formatted_content,
                priority=self.default_priority,
                required=False,
                source=f"rag_retrieval:{res.source.source_type}",
                token_estimate=token_est,
                trust_level=SourceTrustLevel.NORMAL,
                metadata=item_metadata,
            )

            context_items.append(item)
            seen_chunk_ids.add(res.chunk_id)
            seen_text_hashes.add(text_key)
            accumulated_chars += content_len

        return context_items

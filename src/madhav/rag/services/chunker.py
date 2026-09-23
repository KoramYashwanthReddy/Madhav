"""Deterministic, boundary-aware text chunking service."""

import re
from typing import Any

from madhav.rag.domain.chunk import DocumentChunk
from madhav.rag.domain.exceptions import DocumentValidationError


class TextChunker:
    """Splits text into chunks preserving sentence/paragraph boundaries and character offsets."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        minimum_chunk_size: int = 32,
        maximum_chunk_size: int = 2048,
    ) -> None:
        if minimum_chunk_size <= 0:
            raise DocumentValidationError("minimum_chunk_size must be positive.")
        if chunk_size < minimum_chunk_size:
            raise DocumentValidationError("chunk_size must be >= minimum_chunk_size.")
        if maximum_chunk_size < chunk_size:
            raise DocumentValidationError("maximum_chunk_size must be >= chunk_size.")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise DocumentValidationError("chunk_overlap must be >= 0 and < chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.minimum_chunk_size = minimum_chunk_size
        self.maximum_chunk_size = maximum_chunk_size

    def chunk(
        self,
        text: str,
        document_id: str,
        owner_id: str,
        base_metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """Split text into a sequence of DocumentChunk domain models."""
        if not text or not text.strip():
            return []

        base_meta = base_metadata or {}
        slices = self._partition_text(text)

        chunks: list[DocumentChunk] = []
        for idx, (chunk_text, start_idx, end_idx) in enumerate(slices):
            token_est = max(1, len(chunk_text) // 4)
            chunk_meta = dict(base_meta)
            chunk_meta["paragraph_index"] = idx

            chunk = DocumentChunk(
                document_id=document_id,
                owner_id=owner_id,
                chunk_index=idx,
                text=chunk_text,
                character_start=start_idx,
                character_end=end_idx,
                token_estimate=token_est,
                metadata=chunk_meta,
            )
            chunks.append(chunk)

        return chunks

    def _partition_text(self, text: str) -> list[tuple[str, int, int]]:
        """Boundary-aware text partitioning yielding (chunk_text, start_offset, end_offset)."""
        length = len(text)
        if length <= self.chunk_size:
            return [(text.strip(), 0, length)]

        # Split text into atomic units (sentences/paragraphs) with start offsets
        units = self._split_into_units(text)

        slices: list[tuple[str, int, int]] = []
        current_units: list[tuple[str, int, int]] = []
        current_len = 0

        i = 0
        while i < len(units):
            unit_text, start_pos, end_pos = units[i]
            unit_len = len(unit_text)

            # Handle case where single unit is larger than maximum_chunk_size
            if unit_len > self.chunk_size:
                # If we have accumulated text, flush first
                if current_units:
                    chunk_str, c_start, c_end = self._build_slice(current_units)
                    slices.append((chunk_str, c_start, c_end))
                    current_units = []
                    current_len = 0

                # Force split large unit by words
                word_slices = self._split_large_unit(unit_text, start_pos)
                slices.extend(word_slices)
                i += 1
                continue

            if current_len + unit_len <= self.chunk_size or not current_units:
                current_units.append((unit_text, start_pos, end_pos))
                current_len += unit_len
                i += 1
            else:
                # Flush current accumulation as a chunk
                chunk_str, c_start, c_end = self._build_slice(current_units)
                slices.append((chunk_str, c_start, c_end))

                # Compute overlap
                overlap_units: list[tuple[str, int, int]] = []
                overlap_len = 0
                for u in reversed(current_units):
                    if overlap_len + len(u[0]) <= self.chunk_overlap:
                        overlap_units.insert(0, u)
                        overlap_len += len(u[0])
                    else:
                        break

                current_units = overlap_units
                current_len = overlap_len

        if current_units:
            chunk_str, c_start, c_end = self._build_slice(current_units)
            # Avoid duplicate trailing chunk if identical to previous
            if not slices or slices[-1][0] != chunk_str:
                slices.append((chunk_str, c_start, c_end))

        return slices

    def _split_into_units(self, text: str) -> list[tuple[str, int, int]]:
        """Split text into sentence/paragraph boundaries with exact string slice coordinates."""
        pattern = re.compile(r"(?<=[.!?\n])(?=\s|\Z)")
        units: list[tuple[str, int, int]] = []

        last_end = 0
        for match in pattern.finditer(text):
            end = match.end()
            if end > last_end:
                segment = text[last_end:end]
                if segment:
                    units.append((segment, last_end, end))
                last_end = end

        if last_end < len(text):
            segment = text[last_end:]
            if segment:
                units.append((segment, last_end, len(text)))

        if not units:
            units = [(text, 0, len(text))]

        return units

    def _split_large_unit(self, text: str, offset: int) -> list[tuple[str, int, int]]:
        """Split oversized unit into word-boundary chunks."""
        words = text.split(" ")
        slices: list[tuple[str, int, int]] = []

        curr_words: list[str] = []
        curr_len = 0
        sub_start = offset

        for word in words:
            w_len = len(word) + (1 if curr_words else 0)
            if curr_len + w_len <= self.chunk_size or not curr_words:
                curr_words.append(word)
                curr_len += w_len
            else:
                chunk_str = " ".join(curr_words)
                sub_end = sub_start + len(chunk_str)
                slices.append((chunk_str, sub_start, sub_end))

                # Overlap words
                overlap_words = curr_words[-2:] if len(curr_words) >= 2 else []
                curr_words = overlap_words + [word]
                curr_str = " ".join(curr_words)
                curr_len = len(curr_str)
                sub_start = sub_end - len(" ".join(overlap_words))

        if curr_words:
            chunk_str = " ".join(curr_words)
            sub_end = sub_start + len(chunk_str)
            slices.append((chunk_str, sub_start, sub_end))

        return slices

    @staticmethod
    def _build_slice(units: list[tuple[str, int, int]]) -> tuple[str, int, int]:
        """Combine atomic units into a single slice tuple."""
        start = units[0][1]
        end = units[-1][2]
        text_content = "".join(u[0] for u in units).strip()
        return text_content, start, end

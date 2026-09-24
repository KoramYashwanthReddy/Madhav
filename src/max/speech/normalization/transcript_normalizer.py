"""Transcript normalization layer for Module 26 — Speech System.

Performs whitespace cleanup, segment ordering, and provider output normalization
while preserving raw transcript provenance and multilingual code-switching.
"""

from __future__ import annotations

import re

from max.speech.domain.models import Transcript, TranscriptSegment


class TranscriptNormalizer:
    """Normalizes raw speech transcripts into clean text for AI runtime consumption."""

    def normalize_text(self, text: str) -> str:
        """Clean whitespace and formatting while preserving original terms & language."""
        if not text:
            return ""

        # Collapse multiple spaces and line breaks
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned

    def normalize_transcript(self, transcript: Transcript) -> Transcript:
        """Process Transcript model, updating normalized_text and sorting segments."""
        raw = transcript.raw_text or ""
        normalized = self.normalize_text(raw)

        # Sort segments by start_time_seconds
        sorted_segments: list[TranscriptSegment] = sorted(
            transcript.segments, key=lambda s: s.start_time_seconds
        )

        return transcript.model_copy(
            update={
                "raw_text": raw,
                "normalized_text": normalized,
                "segments": sorted_segments,
            }
        )

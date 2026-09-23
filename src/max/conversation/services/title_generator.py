"""Deterministic conversation title generator implementation."""

import re


class DeterministicTitleGenerator:
    """Generates clean, deterministic conversation titles without invoking AI models."""

    def __init__(self, max_length: int = 100) -> None:
        self._max_length = max_length

    def generate_title(self, content: str) -> str:
        """Generate a deterministic title from the first user message content."""

        if not content or not content.strip():
            return "New conversation"

        # 1. Take first non-empty line
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        first_line = lines[0] if lines else content.strip()

        # 2. Collapse internal whitespace
        clean_title = re.sub(r"\s+", " ", first_line).strip()

        # 3. Strip trailing punctuation noise like trailing colons or excess periods
        clean_title = clean_title.rstrip(":")

        if not clean_title:
            return "New conversation"

        # 4. Truncate if exceeds max length
        if len(clean_title) > self._max_length:
            trunc_limit = max(10, self._max_length - 3)
            clean_title = clean_title[:trunc_limit].rstrip() + "..."

        return clean_title

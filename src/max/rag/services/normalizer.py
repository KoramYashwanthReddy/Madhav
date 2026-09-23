"""Text normalization service for RAG & Retrieval Engine."""

import re
import unicodedata

from max.rag.domain.exceptions import DocumentValidationError


class TextNormalizer:
    """Normalizes raw input text while preserving semantic content and structure."""

    @staticmethod
    def normalize(text: str) -> str:
        """Normalize unicode, line breaks, and excessive blank spaces.

        - Converts Unicode representation to NFKC standard form.
        - Standardizes CRLF and CR line endings to LF '\\n'.
        - Trims leading/trailing whitespace per line while preserving paragraph breaks.
        - Removes control characters except newline and tab.
        """
        if not text or not text.strip():
            raise DocumentValidationError("Content for text normalization cannot be empty.")

        # Unicode normalization (NFKC)
        normalized = unicodedata.normalize("NFKC", text)

        # Line ending normalization
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

        # Strip non-printable control characters except \n and \t
        normalized = "".join(
            ch
            for ch in normalized
            if ch == "\n" or ch == "\t" or unicodedata.category(ch)[0] != "C"
        )

        # Normalize trailing spaces on each line
        lines = [line.rstrip() for line in normalized.split("\n")]
        result = "\n".join(lines)

        # Collapse excess blank lines (max 2 consecutive newlines)
        result = re.sub(r"\n{3,}", "\n\n", result).strip()

        if not result:
            raise DocumentValidationError("Content became empty after text normalization.")

        return result

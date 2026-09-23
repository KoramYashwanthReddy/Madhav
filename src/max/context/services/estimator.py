"""TokenEstimator service interface and offline deterministic approximation implementation."""

import math
from typing import Protocol


class TokenEstimator(Protocol):
    """Abstract protocol for context item text token estimation."""

    def estimate(self, text: str) -> int:
        """Estimate token count for a given string."""
        ...


class ApproximateTokenEstimator:
    """Deterministic offline token estimator using word and character count heuristics.

    Note: This is an offline approximation for system context budgeting when an exact
    tokenizer package (e.g. tiktoken/huggingface) is not loaded.
    Formula: max(1, math.ceil(len(words) * 1.3 + (len(chars) - len(words)) / 4))
    """

    def estimate(self, text: str) -> int:
        """Calculate approximate token count deterministically."""
        if not text or not text.strip():
            return 0

        stripped = text.strip()
        words = stripped.split()
        char_count = len(stripped)
        word_count = len(words)

        if word_count == 0:
            return 0

        # Heuristic blending word tokens (~1.3 tokens/word) and non-whitespace char density
        estimate_val = math.ceil(word_count * 1.35 + (char_count / 4.0) * 0.25)
        return max(1, int(estimate_val))

"""Vector similarity utility functions."""

import math

from madhav.rag.domain.exceptions import EmbeddingDimensionMismatchError, EmbeddingProviderError


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate cosine similarity between two float vectors.

    - Numerically safe against precision overflow and zero division.
    - Returns 0.0 if either vector is zero-magnitude.
    - Validates equal dimension size.
    """
    if len(v1) != len(v2):
        raise EmbeddingDimensionMismatchError(expected=len(v1), actual=len(v2))

    dot_product = 0.0
    norm_v1_sq = 0.0
    norm_v2_sq = 0.0

    for x, y in zip(v1, v2, strict=True):
        if math.isnan(x) or math.isinf(x) or math.isnan(y) or math.isinf(y):
            raise EmbeddingProviderError("Cannot compute similarity on non-finite vector values.")
        dot_product += x * y
        norm_v1_sq += x * x
        norm_v2_sq += y * y

    if norm_v1_sq <= 0.0 or norm_v2_sq <= 0.0:
        return 0.0

    norm_product = math.sqrt(norm_v1_sq) * math.sqrt(norm_v2_sq)
    if norm_product <= 0.0:
        return 0.0

    sim = dot_product / norm_product
    # Clamp bounds to [-1.0, 1.0] to eliminate floating point rounding inaccuracies
    return max(-1.0, min(1.0, float(sim)))

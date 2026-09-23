"""Development/Testing deterministic embedding provider.

IMPORTANT:
This provider generates deterministic pseudorandom vectors based on bag-of-words hashing.
It is ONLY for offline unit testing and local development.
It DOES NOT provide production neural network LLM embedding quality.
"""

import hashlib
import math
import re
from typing import Any

from max.rag.domain.embedding import EmbeddingModelInfo
from max.rag.domain.exceptions import EmbeddingProviderError
from max.rag.providers.base import EmbeddingProvider


class DevelopmentEmbeddingProvider(EmbeddingProvider):
    """Deterministic, token-hash embedding provider for local development and testing."""

    def __init__(
        self,
        dimensions: int = 64,
        model_name: str = "dev-hash-embed-v1",
    ) -> None:
        if dimensions <= 0:
            raise EmbeddingProviderError("Embedding dimensions must be a positive integer.")
        self._dimensions = dimensions
        self._model_name = model_name

    async def embed_text(self, text: str) -> list[float]:
        """Generate a deterministic unit-normalized float vector from input text tokens."""
        if not text or not text.strip():
            raise EmbeddingProviderError("Cannot generate embedding for empty text.")

        words = re.findall(r"\w+", text.lower())
        if not words:
            words = [text.strip().lower()]

        combined_vector = [0.0] * self._dimensions
        for word in words:
            w_vec = self._compute_word_vector(word)
            for i in range(self._dimensions):
                combined_vector[i] += w_vec[i]

        return self._l2_normalize(combined_vector)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch embed text payloads deterministically."""
        return [await self.embed_text(txt) for txt in texts]

    def capabilities(self) -> dict[str, Any]:
        """Return provider capabilities."""
        return {
            "provider": "development",
            "is_production": False,
            "supports_batching": True,
            "max_batch_size": 256,
            "dimensions": self._dimensions,
        }

    def model_info(self) -> EmbeddingModelInfo:
        """Return model metadata."""
        return EmbeddingModelInfo(
            provider="development",
            model_name=self._model_name,
            dimensions=self._dimensions,
            version="1.0-dev",
        )

    def _compute_word_vector(self, word: str) -> list[float]:
        """Compute pseudorandom float array derived from word SHA-256 hash seeds."""
        vector: list[float] = []
        seed = word.encode("utf-8")

        for i in range(self._dimensions):
            hash_input = seed + i.to_bytes(4, byteorder="big")
            digest = hashlib.sha256(hash_input).digest()
            raw_int = int.from_bytes(digest[:4], byteorder="big")
            val = (raw_int / 0xFFFFFFFF) * 2.0 - 1.0
            vector.append(val)

        return vector

    @staticmethod
    def _l2_normalize(vector: list[float]) -> list[float]:
        """Normalize vector to unit length L2 norm."""
        norm_sq = sum(x * x for x in vector)
        if norm_sq <= 0.0:
            return vector
        norm = math.sqrt(norm_sq)
        return [x / norm for x in vector]

"""Deterministic duplicate memory detection service implementation."""

import re

from madhav.memory.domain.content import MemoryContent
from madhav.memory.domain.duplicate import MemoryDuplicateResult
from madhav.memory.domain.memory import Memory


class DeterministicDuplicateDetector:
    """Detects duplicate memory content deterministically without LLMs or embeddings."""

    def __init__(self, threshold: float = 0.85) -> None:
        self._threshold = threshold

    def _tokenize(self, text: str) -> set[str]:
        words = re.findall(r"\w+", text.lower())
        return set(words)

    def calculate_similarity(self, content1: MemoryContent, content2: MemoryContent) -> float:
        """Calculate Jaccard token similarity score between two memory content objects."""

        if content1.content_hash == content2.content_hash:
            return 1.0

        tokens1 = self._tokenize(content1.text)
        tokens2 = self._tokenize(content2.text)

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        return len(intersection) / len(union)

    async def check_duplicate(
        self,
        candidate_content: MemoryContent,
        existing_memories: list[Memory],
    ) -> MemoryDuplicateResult:
        """Check candidate memory content against existing memories for duplicates."""

        candidate_hash = candidate_content.content_hash

        for mem in existing_memories:
            if mem.is_deleted():
                continue

            # 1. Check exact content hash match
            if mem.content.content_hash == candidate_hash:
                return MemoryDuplicateResult(
                    is_duplicate=True,
                    existing_memory_id=mem.memory_id,
                    similarity_score=1.0,
                    match_type="exact_hash",
                )

            # 2. Check token overlap similarity ratio
            sim = self.calculate_similarity(candidate_content, mem.content)
            if sim >= self._threshold:
                return MemoryDuplicateResult(
                    is_duplicate=True,
                    existing_memory_id=mem.memory_id,
                    similarity_score=round(sim, 4),
                    match_type="text_overlap",
                )

        return MemoryDuplicateResult(
            is_duplicate=False,
            existing_memory_id=None,
            similarity_score=0.0,
            match_type="none",
        )

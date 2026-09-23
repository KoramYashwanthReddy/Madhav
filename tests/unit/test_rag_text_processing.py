"""Unit tests for Text Normalizer, Text Chunker, and Cosine Similarity."""

import pytest

from max.rag.domain.exceptions import DocumentValidationError, EmbeddingDimensionMismatchError
from max.rag.services.chunker import TextChunker
from max.rag.services.normalizer import TextNormalizer
from max.rag.services.similarity import cosine_similarity


def test_text_normalizer_basic() -> None:
    """Test unicode NFKC, CRLF conversion, and line ending trimming."""
    raw = "Hello\r\nWorld   \n\n\n\nThis is   a test.\r"
    normalized = TextNormalizer.normalize(raw)
    assert "\r" not in normalized
    assert "Hello\nWorld" in normalized
    assert "\n\n\n" not in normalized  # Max 2 consecutive newlines


def test_text_normalizer_empty() -> None:
    """Test normalizer throws on empty/whitespace text."""
    with pytest.raises(DocumentValidationError):
        TextNormalizer.normalize("   \n\t  ")


def test_text_chunker_basic() -> None:
    """Test splitting text into chunks respecting boundary and character offsets."""
    text = (
        "Paragraph 1 is here. It contains sentence one. Sentence two is also here.\n\n"
        "Paragraph 2 is here. It contains sentence three. Sentence four is also here."
    )
    chunker = TextChunker(chunk_size=100, chunk_overlap=20, minimum_chunk_size=10)
    chunks = chunker.chunk(text=text, document_id="doc-123", owner_id="user-1")

    assert len(chunks) >= 2
    assert chunks[0].document_id == "doc-123"
    assert chunks[0].owner_id == "user-1"
    assert chunks[0].chunk_index == 0
    assert chunks[0].character_start == 0
    assert chunks[0].character_end > 0
    assert chunks[0].text in text


def test_text_chunker_deterministic_output() -> None:
    """Test that identical text input produces identical chunk slices."""
    text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    chunker = TextChunker(chunk_size=40, chunk_overlap=10)

    chunks1 = chunker.chunk(text=text, document_id="doc-1", owner_id="user-1")
    chunks2 = chunker.chunk(text=text, document_id="doc-1", owner_id="user-1")

    assert len(chunks1) == len(chunks2)
    for c1, c2 in zip(chunks1, chunks2, strict=True):
        assert c1.text == c2.text
        assert c1.character_start == c2.character_start
        assert c1.character_end == c2.character_end


def test_cosine_similarity_cases() -> None:
    """Test cosine similarity under normal, orthogonal, zero vector, and mismatched conditions."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    v_zero = [0.0, 0.0, 0.0]

    # Identical vectors -> 1.0
    assert pytest.approx(cosine_similarity(v1, v2)) == 1.0

    # Orthogonal vectors -> 0.0
    assert pytest.approx(cosine_similarity(v1, v3)) == 0.0

    # Zero vector comparison -> 0.0
    assert cosine_similarity(v1, v_zero) == 0.0

    # Dimension mismatch
    with pytest.raises(EmbeddingDimensionMismatchError):
        cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0])

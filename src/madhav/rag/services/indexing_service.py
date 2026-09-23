"""Document Indexing Pipeline Service for RAG & Retrieval Engine."""

import hashlib
import logging
from datetime import UTC, datetime

from madhav.rag.domain.document import Document, DocumentSource
from madhav.rag.domain.embedding import EmbeddingVector
from madhav.rag.domain.enums import DocumentStatus
from madhav.rag.domain.exceptions import (
    DocumentIndexingError,
    DocumentNotFoundError,
)
from madhav.rag.providers.base import EmbeddingProvider
from madhav.rag.repositories.document_repository import DocumentRepository
from madhav.rag.services.chunker import TextChunker
from madhav.rag.services.normalizer import TextNormalizer
from madhav.rag.stores.base import VectorStore

logger = logging.getLogger(__name__)


class DocumentIndexingService:
    """Orchestrates document ingestion, normalization, chunking, embedding, and vector storage."""

    def __init__(
        self,
        repository: DocumentRepository,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        chunker: TextChunker | None = None,
    ) -> None:
        self.repository = repository
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.chunker = chunker or TextChunker()

    @staticmethod
    def calculate_content_hash(text: str) -> str:
        """Compute deterministic SHA-256 hash of normalized text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def create_and_index_document(
        self,
        owner_id: str,
        title: str,
        content: str,
        source: DocumentSource,
        document_type: str = "TEXT",
        metadata: dict[str, str | int | float | bool | list[str]] | None = None,
    ) -> Document:
        """Create, save, and index a new document."""
        # 1. Normalize text content
        normalized_content = TextNormalizer.normalize(content)

        # 2. Compute SHA-256 hash
        c_hash = self.calculate_content_hash(normalized_content)

        # 3. Check for existing idempotent document
        existing = await self.repository.get_by_hash(owner_id, c_hash)
        if existing and existing.status == DocumentStatus.INDEXED:
            logger.info("Idempotent document hit for hash %s (doc_id: %s)", c_hash[:8], existing.id)
            return existing

        # 4. Create document entity
        doc = Document(
            owner_id=owner_id,
            title=title,
            content=normalized_content,
            source=source,
            document_type=document_type,  # type: ignore[arg-type]
            status=DocumentStatus.ACTIVE,
            content_hash=c_hash,
            metadata=metadata or {},
        )
        await self.repository.save(doc)

        # 5. Index document
        return await self.index_document(doc.id)

    async def index_document(self, document_id: str) -> Document:
        """Index an existing document by chunking, embedding, and storing in vector store."""
        doc = await self.repository.get_by_id(document_id)
        if not doc:
            raise DocumentNotFoundError(document_id)

        try:
            doc.transition_to(DocumentStatus.INDEXING)
            await self.repository.save(doc)

            # Build metadata payload to attached to chunks
            chunk_base_metadata = dict(doc.metadata)
            chunk_base_metadata.update(
                {
                    "source_type": str(doc.source.source_type),
                    "source_reference": doc.source.source_reference,
                    "title": doc.title,
                    "document_type": str(doc.document_type),
                    "status": str(DocumentStatus.INDEXED),
                }
            )
            if doc.source.uri:
                chunk_base_metadata["uri"] = doc.source.uri

            # Split document into chunks
            chunks = self.chunker.chunk(
                text=doc.content,
                document_id=doc.id,
                owner_id=doc.owner_id,
                base_metadata=chunk_base_metadata,
            )

            if not chunks:
                raise DocumentIndexingError(
                    f"Document '{doc.id}' produced 0 chunks after splitting.",
                    details={"document_id": doc.id},
                )

            # Generate embeddings for chunk texts
            texts = [c.text for c in chunks]
            vectors = await self.embedding_provider.embed_texts(texts)
            model_info = self.embedding_provider.model_info()

            embeddings: list[EmbeddingVector] = []
            for chunk, vec in zip(chunks, vectors, strict=True):
                emb = EmbeddingVector(
                    chunk_id=chunk.chunk_id,
                    document_id=doc.id,
                    owner_id=doc.owner_id,
                    model_info=model_info,
                    vector=vec,
                )
                embeddings.append(emb)

            # Clean out any previous stale chunks in vector store
            await self.vector_store.delete_by_document(doc.id)

            # Store new chunk vectors
            await self.vector_store.upsert_batch(chunks, embeddings)

            # Update document status to INDEXED
            doc.transition_to(DocumentStatus.INDEXED)
            await self.repository.save(doc)

            logger.info("Successfully indexed document %s (%d chunks)", doc.id, len(chunks))
            return doc

        except Exception as exc:
            logger.error("Failed to index document %s: %s", doc.id, str(exc))
            if doc.status == DocumentStatus.INDEXING:
                try:
                    doc.transition_to(DocumentStatus.FAILED)
                    await self.repository.save(doc)
                except Exception:
                    pass
            if isinstance(exc, DocumentIndexingError):
                raise
            raise DocumentIndexingError(
                f"Indexing failed for document '{doc.id}': {exc}",
                details={"document_id": doc.id, "error": str(exc)},
            ) from exc

    async def reindex_document(self, document_id: str, new_content: str | None = None) -> Document:
        """Reindex a document, optionally updating content."""
        doc = await self.repository.get_by_id(document_id)
        if not doc:
            raise DocumentNotFoundError(document_id)

        if new_content is not None:
            normalized = TextNormalizer.normalize(new_content)
            new_hash = self.calculate_content_hash(normalized)
            doc.content = normalized
            doc.content_hash = new_hash
            doc.updated_at = datetime.now(UTC)
            await self.repository.save(doc)

        return await self.index_document(doc.id)

    async def delete_document(self, document_id: str) -> bool:
        """Soft delete document and remove vectors from vector store."""
        doc = await self.repository.get_by_id(document_id)
        if not doc:
            return False

        # Invalidate/delete vector entries
        await self.vector_store.delete_by_document(document_id)

        # Transition document status to DELETED
        doc.transition_to(DocumentStatus.DELETED)
        await self.repository.save(doc)

        logger.info("Deleted document and removed vectors for %s", document_id)
        return True

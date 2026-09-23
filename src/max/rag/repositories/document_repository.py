"""Document Repository implementation for RAG & Retrieval Engine."""

from abc import ABC, abstractmethod

from max.rag.domain.document import Document


class DocumentRepository(ABC):
    """Abstract interface for Document persistence."""

    @abstractmethod
    async def save(self, document: Document) -> Document:
        """Save or update document record."""

    @abstractmethod
    async def get_by_id(self, document_id: str) -> Document | None:
        """Find document by ID."""

    @abstractmethod
    async def get_by_hash(self, owner_id: str, content_hash: str) -> Document | None:
        """Find existing active/indexed document by owner and content hash."""

    @abstractmethod
    async def list_documents(self, owner_id: str, skip: int = 0, limit: int = 50) -> list[Document]:
        """List documents owned by owner_id with pagination."""

    @abstractmethod
    async def count_documents(self, owner_id: str) -> int:
        """Count documents owned by owner_id."""

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete document record."""


class InMemoryDocumentRepository(DocumentRepository):
    """In-memory implementation of DocumentRepository."""

    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}

    async def save(self, document: Document) -> Document:
        """Save document instance."""
        self._documents[document.id] = document
        return document

    async def get_by_id(self, document_id: str) -> Document | None:
        """Retrieve document by ID."""
        return self._documents.get(document_id)

    async def get_by_hash(self, owner_id: str, content_hash: str) -> Document | None:
        """Find document by owner_id and content_hash (for idempotency)."""
        for doc in self._documents.values():
            if doc.owner_id == owner_id and doc.content_hash == content_hash:
                return doc
        return None

    async def list_documents(self, owner_id: str, skip: int = 0, limit: int = 50) -> list[Document]:
        """List documents owned by owner_id."""
        matching = [
            doc for doc in self._documents.values() if doc.owner_id == owner_id
        ]
        matching.sort(key=lambda d: d.created_at, reverse=True)
        return matching[skip : skip + limit]

    async def count_documents(self, owner_id: str) -> int:
        """Count documents owned by owner_id."""
        return sum(1 for doc in self._documents.values() if doc.owner_id == owner_id)

    async def delete(self, document_id: str) -> bool:
        """Delete document by ID."""
        if document_id in self._documents:
            del self._documents[document_id]
            return True
        return False

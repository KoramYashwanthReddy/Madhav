"""In-memory repositories for Module 24 — Document Intelligence."""

from datetime import UTC, datetime
from typing import Any

from max.document.domain.exceptions import DocumentNotFoundError
from max.document.domain.models import (
    Document,
    DocumentProcessingJob,
    DocumentVersion,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class DocumentRepository:
    """In-memory CRUD store for Document objects."""

    def __init__(self) -> None:
        self._store: dict[str, Document] = {}
        self._hash_idx: dict[str, str] = {}  # hash -> doc_id

    def save(self, doc: Document) -> Document:
        doc.updated_at = _utc_now()
        self._store[doc.id] = doc
        if doc.content_hash:
            self._hash_idx[doc.content_hash] = doc.id
        return doc

    def get(self, doc_id: str) -> Document:
        try:
            return self._store[doc_id]
        except KeyError:
            raise DocumentNotFoundError(
                f"Document '{doc_id}' not found.",
                details={"document_id": doc_id},
            )

    def get_by_hash(self, content_hash: str) -> Document | None:
        doc_id = self._hash_idx.get(content_hash)
        if doc_id and doc_id in self._store:
            return self._store[doc_id]
        return None

    def list_all(
        self,
        owner_id: str | None = None,
        doc_type: str | None = None,
        format_ext: str | None = None,
    ) -> list[Document]:
        docs = list(self._store.values())
        if owner_id is not None:
            docs = [d for d in docs if d.owner_id == owner_id]
        if doc_type is not None:
            docs = [d for d in docs if d.doc_type.value == doc_type]
        if format_ext is not None:
            docs = [d for d in docs if d.format.value == format_ext]
        return docs

    def delete(self, doc_id: str) -> bool:
        doc = self._store.pop(doc_id, None)
        if doc:
            if doc.content_hash in self._hash_idx:
                del self._hash_idx[doc.content_hash]
            return True
        return False


class DocumentVersionRepository:
    """In-memory store for DocumentVersion history snapshots."""

    def __init__(self) -> None:
        self._store: dict[str, DocumentVersion] = {}

    def save(self, version: DocumentVersion) -> DocumentVersion:
        self._store[version.version_id] = version
        return version

    def get(self, version_id: str) -> DocumentVersion:
        try:
            return self._store[version_id]
        except KeyError:
            raise DocumentNotFoundError(
                f"Document version '{version_id}' not found.",
                details={"version_id": version_id},
            )

    def list_for_document(self, document_id: str) -> list[DocumentVersion]:
        versions = [v for v in self._store.values() if v.document_id == document_id]
        return sorted(versions, key=lambda v: v.version_number)


class DocumentProcessingRepository:
    """In-memory store for DocumentProcessingJob tracking records."""

    def __init__(self) -> None:
        self._store: dict[str, DocumentProcessingJob] = {}

    def save(self, job: DocumentProcessingJob) -> DocumentProcessingJob:
        self._store[job.job_id] = job
        return job

    def get(self, job_id: str) -> DocumentProcessingJob:
        try:
            return self._store[job_id]
        except KeyError:
            raise DocumentNotFoundError(
                f"Processing job '{job_id}' not found.",
                details={"job_id": job_id},
            )

    def get_by_document(self, document_id: str) -> DocumentProcessingJob | None:
        jobs = [j for j in self._store.values() if j.document_id == document_id]
        return jobs[-1] if jobs else None


class DocumentAuditRepository:
    """Append-only audit log for Document Intelligence events."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def record(self, document_id: str, action: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        event = {
            "document_id": document_id,
            "action": action,
            "timestamp": _utc_now().isoformat(),
            "details": details or {},
        }
        self._events.append(event)
        return event

    def list_for_document(self, document_id: str) -> list[dict[str, Any]]:
        return [e for e in self._events if e["document_id"] == document_id]

"""Repositories package for Module 24 — Document Intelligence."""

from max.document.repositories.repositories import (
    DocumentAuditRepository,
    DocumentProcessingRepository,
    DocumentRepository,
    DocumentVersionRepository,
)

__all__ = [
    "DocumentRepository",
    "DocumentVersionRepository",
    "DocumentProcessingRepository",
    "DocumentAuditRepository",
]

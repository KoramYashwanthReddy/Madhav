"""Module 24 — Document Intelligence: Adapters package."""

from max.document.adapters.filesystem_adapter import DocumentFilesystemAdapter
from max.document.adapters.rag_adapter import DocumentRAGAdapter

__all__ = [
    "DocumentFilesystemAdapter",
    "DocumentRAGAdapter",
]

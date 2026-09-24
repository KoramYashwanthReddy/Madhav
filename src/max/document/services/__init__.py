"""Module 24 — Document Intelligence: Services package."""

from max.document.services.document_service import DocumentService
from max.document.services.tool_integration import register_document_tools

__all__ = [
    "DocumentService",
    "register_document_tools",
]

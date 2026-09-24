"""Global dependency injection container for Module 24 — Document Intelligence."""

from max.config.settings import get_settings
from max.document.adapters.filesystem_adapter import DocumentFilesystemAdapter
from max.document.adapters.rag_adapter import DocumentRAGAdapter
from max.document.converters.base import BaseDocumentConverter
from max.document.generators.base import BaseDocumentGenerator
from max.document.parsers.registry import DocumentParserRegistry
from max.document.repositories.repositories import (
    DocumentAuditRepository,
    DocumentProcessingRepository,
    DocumentRepository,
    DocumentVersionRepository,
)
from max.document.security.prompt_injection import DocumentSecurityEnforcer
from max.document.services.document_service import DocumentService


class DocumentContainer:
    """Dependency injection container for the Document Intelligence subsystem."""

    def __init__(self) -> None:
        cfg = get_settings().document
        self.settings = cfg

        # Repositories
        self.doc_repo = DocumentRepository()
        self.version_repo = DocumentVersionRepository()
        self.job_repo = DocumentProcessingRepository()
        self.audit_repo = DocumentAuditRepository()

        # Infrastructure components
        self.parser_registry = DocumentParserRegistry()
        self.filesystem_adapter = DocumentFilesystemAdapter()
        self.rag_adapter = DocumentRAGAdapter()
        self.generator = BaseDocumentGenerator()
        self.converter = BaseDocumentConverter()
        self.security_enforcer = DocumentSecurityEnforcer()

        # Master service facade
        self.service = DocumentService(
            doc_repo=self.doc_repo,
            version_repo=self.version_repo,
            job_repo=self.job_repo,
            audit_repo=self.audit_repo,
            parser_registry=self.parser_registry,
            filesystem_adapter=self.filesystem_adapter,
            generator=self.generator,
            converter=self.converter,
            security_enforcer=self.security_enforcer,
            max_file_size_mb=float(cfg.max_document_size_mb),
        )


_container_instance: DocumentContainer | None = None


def get_document_container() -> DocumentContainer:
    """Retrieve or initialize the global DocumentContainer instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = DocumentContainer()
    return _container_instance


def reset_document_container() -> None:
    """Reset the global DocumentContainer instance (used for test isolation)."""
    global _container_instance
    _container_instance = None

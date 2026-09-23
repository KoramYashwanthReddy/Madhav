"""REST API endpoints for Module 10 RAG & Retrieval Engine."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from madhav.config.settings import get_settings
from madhav.rag.domain.document import Document, DocumentSource
from madhav.rag.domain.enums import DocumentType
from madhav.rag.domain.exceptions import RAGError
from madhav.rag.domain.query import RetrievalFilter, RetrievalQuery
from madhav.rag.providers.dev_provider import DevelopmentEmbeddingProvider
from madhav.rag.repositories.document_repository import InMemoryDocumentRepository
from madhav.rag.schemas.requests import (
    DocumentCreateRequest,
    DocumentUpdateRequest,
    RetrievalSearchRequest,
)
from madhav.rag.schemas.responses import (
    CitationResponse,
    DocumentListResponse,
    DocumentResponse,
    RAGStatusResponse,
    RetrievalResultResponse,
    RetrievalSearchResponse,
)
from madhav.rag.services.indexing_service import DocumentIndexingService
from madhav.rag.services.retrieval_service import RetrievalService
from madhav.rag.stores.memory_store import InMemoryVectorStore

router = APIRouter(prefix="/rag", tags=["RAG & Retrieval Engine"])

_indexing_service_instance: DocumentIndexingService | None = None
_retrieval_service_instance: RetrievalService | None = None


def get_rag_services() -> tuple[DocumentIndexingService, RetrievalService]:
    """Dependency provider returning active RAG service singletons."""
    global _indexing_service_instance, _retrieval_service_instance
    if _indexing_service_instance is None or _retrieval_service_instance is None:
        settings = get_settings()
        repo = InMemoryDocumentRepository()
        vstore = InMemoryVectorStore(expected_dimensions=settings.rag.embedding_dimensions)
        provider = DevelopmentEmbeddingProvider(dimensions=settings.rag.embedding_dimensions)

        _indexing_service_instance = DocumentIndexingService(
            repository=repo,
            vector_store=vstore,
            embedding_provider=provider,
        )
        _retrieval_service_instance = RetrievalService(
            vector_store=vstore,
            embedding_provider=provider,
            default_top_k=settings.rag.default_top_k,
            max_top_k=settings.rag.max_top_k,
            default_minimum_score=settings.rag.minimum_score,
        )
    return _indexing_service_instance, _retrieval_service_instance


def get_indexing_service(
    services: tuple[DocumentIndexingService, RetrievalService] = Depends(get_rag_services),
) -> DocumentIndexingService:
    """Dependency provider returning DocumentIndexingService."""
    return services[0]


def get_retrieval_service(
    services: tuple[DocumentIndexingService, RetrievalService] = Depends(get_rag_services),
) -> RetrievalService:
    """Dependency provider returning RetrievalService."""
    return services[1]


def set_rag_services(
    indexing_service: DocumentIndexingService | None,
    retrieval_service: RetrievalService | None,
) -> None:
    """Helper to set or reset singleton services for unit testing."""
    global _indexing_service_instance, _retrieval_service_instance
    _indexing_service_instance = indexing_service
    _retrieval_service_instance = retrieval_service


def _map_doc_response(doc: Document) -> DocumentResponse:
    """Helper to map Document entity to DocumentResponse schema."""
    return DocumentResponse(
        id=doc.id,
        owner_id=doc.owner_id,
        title=doc.title,
        content=doc.content,
        source_type=doc.source.source_type,
        source_reference=doc.source.source_reference,
        document_type=doc.document_type,
        status=doc.status,
        content_hash=doc.content_hash,
        metadata=doc.metadata,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        indexed_at=doc.indexed_at,
    )


# --- DOCUMENT ENDPOINTS ---

@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def create_document(
    req: DocumentCreateRequest,
    indexing_service: DocumentIndexingService = Depends(get_indexing_service),
) -> DocumentResponse:
    """Ingest and index a new document."""
    try:
        source = DocumentSource(
            source_type=req.source.source_type,
            source_reference=req.source.source_reference,
            uri=req.source.uri,
        )
        doc_type_str = (
            req.document_type.value
            if isinstance(req.document_type, DocumentType)
            else str(req.document_type)
        )
        doc = await indexing_service.create_and_index_document(
            owner_id=req.owner_id,
            title=req.title,
            content=req.content,
            source=source,
            document_type=doc_type_str,
            metadata=req.metadata,
        )
        return _map_doc_response(doc)
    except RAGError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    owner_id: str = Query(..., description="Owner user ID"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    indexing_service: DocumentIndexingService = Depends(get_indexing_service),
) -> DocumentListResponse:
    """List documents for an owner."""
    try:
        docs = await indexing_service.repository.list_documents(owner_id, skip=skip, limit=limit)
        total = await indexing_service.repository.count_documents(owner_id)
        return DocumentListResponse(
            documents=[_map_doc_response(d) for d in docs],
            total=total,
            skip=skip,
            limit=limit,
        )
    except RAGError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    indexing_service: DocumentIndexingService = Depends(get_indexing_service),
) -> DocumentResponse:
    """Retrieve document details by ID."""
    doc = await indexing_service.repository.get_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Document '{document_id}' not found.",
                "code": "DOCUMENT_NOT_FOUND",
            },
        )
    return _map_doc_response(doc)


@router.patch("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    req: DocumentUpdateRequest,
    indexing_service: DocumentIndexingService = Depends(get_indexing_service),
) -> DocumentResponse:
    """Update document properties and reindex if requested."""
    try:
        doc = await indexing_service.repository.get_by_id(document_id)
        if not doc:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Document '{document_id}' not found.",
                    "code": "DOCUMENT_NOT_FOUND",
                },
            )
        if req.title:
            doc.title = req.title
        if req.metadata:
            doc.metadata.update(req.metadata)
        await indexing_service.repository.save(doc)

        if req.content is not None or req.reindex:
            doc = await indexing_service.reindex_document(document_id, new_content=req.content)

        return _map_doc_response(doc)
    except RAGError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    indexing_service: DocumentIndexingService = Depends(get_indexing_service),
) -> Response:
    """Delete document and purge vectors."""
    try:
        deleted = await indexing_service.delete_document(document_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Document '{document_id}' not found.",
                    "code": "DOCUMENT_NOT_FOUND",
                },
            )
        return Response(status_code=204)
    except RAGError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post("/documents/{document_id}/index", response_model=DocumentResponse)
async def index_document_endpoint(
    document_id: str,
    indexing_service: DocumentIndexingService = Depends(get_indexing_service),
) -> DocumentResponse:
    """Trigger indexing for an existing document."""
    try:
        doc = await indexing_service.index_document(document_id)
        return _map_doc_response(doc)
    except RAGError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post("/documents/{document_id}/reindex", response_model=DocumentResponse)
async def reindex_document_endpoint(
    document_id: str,
    indexing_service: DocumentIndexingService = Depends(get_indexing_service),
) -> DocumentResponse:
    """Trigger reindexing for an existing document."""
    try:
        doc = await indexing_service.reindex_document(document_id)
        return _map_doc_response(doc)
    except RAGError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


# --- RETRIEVAL ENDPOINTS ---

@router.post("/search", response_model=RetrievalSearchResponse)
async def search_retrieval(
    req: RetrievalSearchRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> RetrievalSearchResponse:
    """Execute vector similarity search across indexed documents."""
    try:
        filter_domain = RetrievalFilter(
            document_type=req.filters.document_type,
            source_type=req.filters.source_type,
            document_id=req.filters.document_id,
            collection_id=req.filters.collection_id,
            tags=req.filters.tags,
            status=req.filters.status,
        )

        query = RetrievalQuery(
            query_text=req.query_text,
            owner_id=req.owner_id,
            top_k=req.top_k,
            minimum_score=req.minimum_score,
            filters=filter_domain,
            include_archived=req.include_archived,
            include_deleted=req.include_deleted,
        )

        resp = await retrieval_service.retrieve(query)

        results_schema = [
            RetrievalResultResponse(
                chunk_id=res.chunk_id,
                document_id=res.document_id,
                text=res.text,
                score=res.score,
                rank=res.rank,
                metadata=res.metadata,
                citation=CitationResponse(
                    document_id=res.citation.document_id,
                    chunk_id=res.citation.chunk_id,
                    source_type=res.citation.source_type,
                    source_reference=res.citation.source_reference,
                    title=res.citation.title,
                    location=res.citation.location,
                    score=res.citation.score,
                ),
            )
            for res in resp.results
        ]

        citations_schema = [
            CitationResponse(
                document_id=c.document_id,
                chunk_id=c.chunk_id,
                source_type=c.source_type,
                source_reference=c.source_reference,
                title=c.title,
                location=c.location,
                score=c.score,
            )
            for c in resp.citations
        ]

        return RetrievalSearchResponse(
            query_text=resp.query.query_text,
            owner_id=resp.query.owner_id,
            results=results_schema,
            total_retrieved=resp.total_retrieved,
            citations=citations_schema,
            execution_time_ms=resp.execution_time_ms,
            metadata=resp.metadata,
        )
    except RAGError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post("/retrieve", response_model=RetrievalSearchResponse)
async def retrieve_alias(
    req: RetrievalSearchRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> RetrievalSearchResponse:
    """Alias endpoint for vector similarity search."""
    return await search_retrieval(req, retrieval_service)


# --- STATUS ENDPOINT ---

@router.get("/status", response_model=RAGStatusResponse)
async def rag_status(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> RAGStatusResponse:
    """Get subsystem health and active provider status."""
    st = await retrieval_service.get_status()
    return RAGStatusResponse(
        rag_enabled=st["rag_enabled"],
        embedding_provider=st["embedding_provider"],
        embedding_model=st["embedding_model"],
        embedding_dimensions=st["embedding_dimensions"],
        vector_store_provider=st["vector_store_provider"],
        vector_store_health=st["vector_store_health"],
        default_top_k=st["default_top_k"],
        max_top_k=st["max_top_k"],
        minimum_score=st["default_minimum_score"],
    )

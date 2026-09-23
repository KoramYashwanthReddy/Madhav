"""Integration tests for RAG API routes."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from madhav.api.router import register_routers
from madhav.rag.api.routes import set_rag_services
from madhav.rag.providers.dev_provider import DevelopmentEmbeddingProvider
from madhav.rag.repositories.document_repository import InMemoryDocumentRepository
from madhav.rag.services.indexing_service import DocumentIndexingService
from madhav.rag.services.retrieval_service import RetrievalService
from madhav.rag.stores.memory_store import InMemoryVectorStore


@pytest.fixture
def api_client():
    """Create test client with isolated RAG services."""
    app = FastAPI()
    register_routers(app)

    repo = InMemoryDocumentRepository()
    vstore = InMemoryVectorStore(expected_dimensions=64)
    provider = DevelopmentEmbeddingProvider(dimensions=64)
    indexing = DocumentIndexingService(
        repository=repo, vector_store=vstore, embedding_provider=provider
    )
    retrieval = RetrievalService(vector_store=vstore, embedding_provider=provider)

    set_rag_services(indexing, retrieval)

    client = TestClient(app)
    yield client
    set_rag_services(None, None)


def test_rag_status_endpoint(api_client: TestClient) -> None:
    """Test GET /api/v1/rag/status diagnostic endpoint."""
    resp = api_client.get("/api/v1/rag/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rag_enabled"] is True
    assert data["embedding_provider"] == "development"
    assert data["vector_store_provider"] == "memory"


def test_document_crud_and_indexing_flow(api_client: TestClient) -> None:
    """Test POST, GET, PATCH, DELETE endpoints for documents."""
    # 1. Create document
    create_payload = {
        "owner_id": "test_owner",
        "title": "API Spec Document",
        "content": "This document specifies REST endpoints for the platform.",
        "source": {
            "source_type": "FILE",
            "source_reference": "spec.md",
        },
        "document_type": "MARKDOWN",
        "metadata": {"category": "docs"},
    }
    create_resp = api_client.post("/api/v1/rag/documents", json=create_payload)
    assert create_resp.status_code == 201
    doc_data = create_resp.json()
    doc_id = doc_data["id"]
    assert doc_data["status"] == "INDEXED"

    # 2. Get document
    get_resp = api_client.get(f"/api/v1/rag/documents/{doc_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "API Spec Document"

    # 3. List documents
    list_resp = api_client.get("/api/v1/rag/documents", params={"owner_id": "test_owner"})
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    # 4. Search retrieval
    search_payload = {
        "query_text": "REST endpoints specification",
        "owner_id": "test_owner",
        "top_k": 5,
    }
    search_resp = api_client.post("/api/v1/rag/search", json=search_payload)
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total_retrieved"] > 0
    assert search_data["results"][0]["document_id"] == doc_id
    assert search_data["results"][0]["citation"]["title"] == "API Spec Document"

    # 5. Delete document
    del_resp = api_client.delete(f"/api/v1/rag/documents/{doc_id}")
    assert del_resp.status_code == 204

    # 6. Verify deleted
    get_after_del = api_client.get(f"/api/v1/rag/documents/{doc_id}")
    assert get_after_del.json()["status"] == "DELETED"

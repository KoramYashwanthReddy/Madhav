"""Integration tests for Module 09 Personal Knowledge Engine REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from madhav.knowledge.api.routes import set_knowledge_service
from madhav.knowledge.repositories.memory import InMemoryKnowledgeRepository
from madhav.knowledge.services.knowledge_service import KnowledgeService
from madhav.main import app


@pytest.fixture(autouse=True)
def reset_knowledge_service() -> None:
    """Ensure clean KnowledgeService instance for every test."""
    repo = InMemoryKnowledgeRepository()
    set_knowledge_service(
        KnowledgeService(
            entity_repo=repo,
            fact_repo=repo,
            relation_repo=repo,
            collection_repo=repo,
            version_repo=repo,
        )
    )


def test_api_entity_fact_relation_collection_flow() -> None:
    """API integration flow testing entities, facts, relations, collections, search, and summary."""

    client = TestClient(app)

    # 1. Create collection
    col_resp = client.post(
        "/api/v1/knowledge/collections",
        json={"name": "Core Technologies", "description": "Programming languages and frameworks"},
    )
    assert col_resp.status_code == 201
    col_id = col_resp.json()["id"]

    # 2. Create entities
    e1_resp = client.post(
        "/api/v1/knowledge/entities",
        json={
            "type": "technology",
            "name": "Python",
            "description": "High-level programming language",
            "collection_id": col_id,
        },
    )
    assert e1_resp.status_code == 201
    e1_id = e1_resp.json()["id"]

    e2_resp = client.post(
        "/api/v1/knowledge/entities",
        json={
            "type": "project",
            "name": "Madhav Personal AI",
            "description": "Modular AI System",
            "collection_id": col_id,
        },
    )
    assert e2_resp.status_code == 201
    e2_id = e2_resp.json()["id"]

    # 3. Create fact for e1
    fact_resp = client.post(
        "/api/v1/knowledge/facts",
        json={
            "entity_id": e1_id,
            "subject": "Python",
            "predicate": "version",
            "object": "3.12",
            "value": "3.12",
            "value_type": "text",
        },
    )
    assert fact_resp.status_code == 201

    # 4. Create relation link (Madhav Personal AI -> USES -> Python)
    rel_resp = client.post(
        "/api/v1/knowledge/relations",
        json={
            "source_entity_id": e2_id,
            "relation_type": "uses",
            "target_entity_id": e1_id,
        },
    )
    assert rel_resp.status_code == 201

    # 5. Get entity summary projection for e2
    sum_resp = client.get(f"/api/v1/knowledge/entities/{e2_id}/summary")
    assert sum_resp.status_code == 200
    sum_data = sum_resp.json()
    assert sum_data["entity"]["id"] == e2_id
    assert len(sum_data["outgoing_relations"]) == 1
    assert sum_data["outgoing_relations"][0]["target_entity_id"] == e1_id

    # 6. Search entities
    search_resp = client.post("/api/v1/knowledge/search", json={"query": "python"})
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 1

    # 7. Archive entity
    arch_resp = client.post(f"/api/v1/knowledge/entities/{e1_id}/archive")
    assert arch_resp.status_code == 200
    assert arch_resp.json()["status"] == "archived"

    # 8. Soft Delete entity
    del_resp = client.delete(f"/api/v1/knowledge/entities/{e1_id}")
    assert del_resp.status_code == 204

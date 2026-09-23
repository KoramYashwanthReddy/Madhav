"""REST API endpoints for Module 09 Personal Knowledge Engine."""

from fastapi import APIRouter, Depends, HTTPException, Query

from madhav.knowledge.domain.enums import (
    KnowledgeConfidence,
    KnowledgeEntityType,
    KnowledgeRelationType,
    KnowledgeStatus,
)
from madhav.knowledge.domain.filter import KnowledgeSearchFilter
from madhav.knowledge.domain.metadata import KnowledgeMetadata
from madhav.knowledge.exceptions import KnowledgeError
from madhav.knowledge.repositories.memory import InMemoryKnowledgeRepository
from madhav.knowledge.schemas.requests import (
    CreateCollectionRequest,
    CreateEntityRequest,
    CreateFactRequest,
    CreateRelationRequest,
    KnowledgeSearchRequest,
    UpdateCollectionRequest,
    UpdateEntityRequest,
    UpdateFactRequest,
)
from madhav.knowledge.schemas.responses import (
    KnowledgeCollectionResponse,
    KnowledgeEntityResponse,
    KnowledgeFactResponse,
    KnowledgeListResponse,
    KnowledgeRelationResponse,
    KnowledgeSummaryResponse,
)
from madhav.knowledge.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Personal Knowledge Engine"])

_knowledge_service_instance: KnowledgeService | None = None


def get_knowledge_service() -> KnowledgeService:
    """Dependency provider returning singleton KnowledgeService instance."""
    global _knowledge_service_instance
    if _knowledge_service_instance is None:
        repo = InMemoryKnowledgeRepository()
        _knowledge_service_instance = KnowledgeService(
            entity_repo=repo,
            fact_repo=repo,
            relation_repo=repo,
            collection_repo=repo,
            version_repo=repo,
        )
    return _knowledge_service_instance


def set_knowledge_service(service: KnowledgeService | None) -> None:
    """Helper to set or reset singleton KnowledgeService instance for testing."""
    global _knowledge_service_instance
    _knowledge_service_instance = service


# --- ENTITIES ---

@router.post("/entities", response_model=KnowledgeEntityResponse, status_code=201)
async def create_entity(
    req: CreateEntityRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeEntityResponse:
    """Create a new Knowledge Entity."""
    try:
        metadata = KnowledgeMetadata(
            tags=req.tags,
            external_reference=req.external_reference,
            source_reference=req.source_reference,
            custom_metadata=req.custom_metadata,
        )
        entity = await service.create_entity(
            owner_id="default_owner",
            type=req.type,
            name=req.name,
            description=req.description,
            confidence=req.confidence,
            scope=req.scope,
            collection_id=req.collection_id,
            metadata=metadata,
            allow_duplicate=req.allow_duplicate,
        )
        return KnowledgeEntityResponse.from_domain(entity)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get("/entities", response_model=KnowledgeListResponse[KnowledgeEntityResponse])
async def list_entities(
    query: str | None = Query(default=None),
    type: KnowledgeEntityType | None = Query(default=None),
    status: KnowledgeStatus | None = Query(default=KnowledgeStatus.ACTIVE),
    confidence: KnowledgeConfidence | None = Query(default=None),
    collection_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeListResponse[KnowledgeEntityResponse]:
    """List entities with filtering and pagination."""
    try:
        filter_spec = KnowledgeSearchFilter(
            owner_id="default_owner",
            query=query,
            entity_type=type,
            status=status,
            confidence=confidence,
            collection_id=collection_id,
            page=page,
            page_size=page_size,
        )
        entities, total = await service.list_entities(filter_spec)
        return KnowledgeListResponse(
            items=[KnowledgeEntityResponse.from_domain(e) for e in entities],
            total=total,
            page=page,
            page_size=page_size,
        )
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get("/entities/{entity_id}", response_model=KnowledgeEntityResponse)
async def get_entity(
    entity_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeEntityResponse:
    """Get entity details by ID."""
    try:
        entity = await service.get_entity(entity_id, owner_id="default_owner")
        return KnowledgeEntityResponse.from_domain(entity)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.patch("/entities/{entity_id}", response_model=KnowledgeEntityResponse)
async def update_entity(
    entity_id: str,
    req: UpdateEntityRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeEntityResponse:
    """Update entity properties."""
    try:
        has_meta_updates = (
            req.tags is not None
            or req.external_reference is not None
            or req.custom_metadata is not None
        )
        metadata = (
            KnowledgeMetadata(
                tags=req.tags or [],
                external_reference=req.external_reference,
                custom_metadata=req.custom_metadata or {},
            )
            if has_meta_updates
            else None
        )
        updated = await service.update_entity(
            entity_id=entity_id,
            owner_id="default_owner",
            name=req.name,
            description=req.description,
            confidence=req.confidence,
            collection_id=req.collection_id,
            metadata=metadata,
            change_reason=req.change_reason,
        )
        return KnowledgeEntityResponse.from_domain(updated)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.delete("/entities/{entity_id}", status_code=204)
async def delete_entity(
    entity_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> None:
    """Delete entity (soft delete)."""
    try:
        await service.delete_entity(entity_id, owner_id="default_owner", soft_delete=True)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post("/entities/{entity_id}/archive", response_model=KnowledgeEntityResponse)
async def archive_entity(
    entity_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeEntityResponse:
    """Archive entity."""
    try:
        archived = await service.archive_entity(entity_id, owner_id="default_owner")
        return KnowledgeEntityResponse.from_domain(archived)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post("/entities/{entity_id}/restore", response_model=KnowledgeEntityResponse)
async def restore_entity(
    entity_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeEntityResponse:
    """Restore entity."""
    try:
        restored = await service.restore_entity(entity_id, owner_id="default_owner")
        return KnowledgeEntityResponse.from_domain(restored)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get("/entities/{entity_id}/summary", response_model=KnowledgeSummaryResponse)
async def get_entity_summary(
    entity_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeSummaryResponse:
    """Get aggregated entity summary projection."""
    try:
        summary = await service.get_knowledge_summary(entity_id, owner_id="default_owner")
        col_resp = (
            KnowledgeCollectionResponse.from_domain(summary.collection)
            if summary.collection
            else None
        )
        return KnowledgeSummaryResponse(
            entity=KnowledgeEntityResponse.from_domain(summary.entity),
            facts=[KnowledgeFactResponse.from_domain(f) for f in summary.facts],
            outgoing_relations=[
                KnowledgeRelationResponse.from_domain(r) for r in summary.outgoing_relations
            ],
            incoming_relations=[
                KnowledgeRelationResponse.from_domain(r) for r in summary.incoming_relations
            ],
            collection=col_resp,
            version_count=summary.version_count,
        )
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get("/entities/{entity_id}/facts", response_model=list[KnowledgeFactResponse])
async def list_entity_facts(
    entity_id: str,
    status: KnowledgeStatus | None = Query(default=KnowledgeStatus.ACTIVE),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> list[KnowledgeFactResponse]:
    """List facts associated with an entity."""
    try:
        facts = await service.list_facts_by_entity(
            entity_id, owner_id="default_owner", status=status
        )
        return [KnowledgeFactResponse.from_domain(f) for f in facts]

    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get("/entities/{entity_id}/relations", response_model=list[KnowledgeRelationResponse])
async def list_entity_relations(
    entity_id: str,
    direction: str = Query(default="outgoing", pattern="^(outgoing|incoming|all)$"),
    relation_type: KnowledgeRelationType | None = Query(default=None),
    status: KnowledgeStatus | None = Query(default=KnowledgeStatus.ACTIVE),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> list[KnowledgeRelationResponse]:

    """List relations associated with an entity."""
    try:
        rels: list[KnowledgeRelationResponse] = []
        if direction in ("outgoing", "all"):
            out = await service.list_outgoing_relations(
                entity_id, owner_id="default_owner", relation_type=relation_type, status=status
            )
            rels.extend(KnowledgeRelationResponse.from_domain(r) for r in out)
        if direction in ("incoming", "all"):
            inc = await service.list_incoming_relations(
                entity_id, owner_id="default_owner", relation_type=relation_type, status=status
            )
            rels.extend(KnowledgeRelationResponse.from_domain(r) for r in inc)
        return rels
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


# --- FACTS ---

@router.post("/facts", response_model=KnowledgeFactResponse, status_code=201)
async def create_fact(
    req: CreateFactRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeFactResponse:
    """Create a new Knowledge Fact."""
    try:
        fact = await service.create_fact(
            owner_id="default_owner",
            entity_id=req.entity_id,
            subject=req.subject,
            predicate=req.predicate,
            object=req.object,
            value=req.value,
            value_type=req.value_type,
            confidence=req.confidence,
            source_type=req.source_type,
            source_reference=req.source_reference,
            valid_from=req.valid_from,
            valid_until=req.valid_until,
            allow_duplicate=req.allow_duplicate,
        )
        return KnowledgeFactResponse.from_domain(fact)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get("/facts/{fact_id}", response_model=KnowledgeFactResponse)
async def get_fact(
    fact_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeFactResponse:
    """Get fact details by ID."""
    try:
        fact = await service.get_fact(fact_id, owner_id="default_owner")
        return KnowledgeFactResponse.from_domain(fact)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.patch("/facts/{fact_id}", response_model=KnowledgeFactResponse)
async def update_fact(
    fact_id: str,
    req: UpdateFactRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeFactResponse:
    """Update fact assertion."""
    try:
        updated = await service.update_fact(
            fact_id=fact_id,
            owner_id="default_owner",
            subject=req.subject,
            predicate=req.predicate,
            object=req.object,
            value=req.value,
            value_type=req.value_type,
            confidence=req.confidence,
            valid_from=req.valid_from,
            valid_until=req.valid_until,
            change_reason=req.change_reason,
        )
        return KnowledgeFactResponse.from_domain(updated)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.delete("/facts/{fact_id}", status_code=204)
async def delete_fact(
    fact_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> None:
    """Delete fact (soft delete)."""
    try:
        await service.delete_fact(fact_id, owner_id="default_owner", soft_delete=True)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


# --- RELATIONS ---

@router.post("/relations", response_model=KnowledgeRelationResponse, status_code=201)
async def create_relation(
    req: CreateRelationRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeRelationResponse:
    """Create a new relation link."""
    try:
        metadata = KnowledgeMetadata(tags=req.tags, custom_metadata=req.custom_metadata)
        rel = await service.create_relation(
            owner_id="default_owner",
            source_entity_id=req.source_entity_id,
            relation_type=req.relation_type,
            target_entity_id=req.target_entity_id,
            confidence=req.confidence,
            source_type=req.source_type,
            source_reference=req.source_reference,
            metadata=metadata,
        )
        return KnowledgeRelationResponse.from_domain(rel)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get("/relations/{relation_id}", response_model=KnowledgeRelationResponse)
async def get_relation(
    relation_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeRelationResponse:
    """Get relation details by ID."""
    try:
        rel = await service.get_relation(relation_id, owner_id="default_owner")
        return KnowledgeRelationResponse.from_domain(rel)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.delete("/relations/{relation_id}", status_code=204)
async def delete_relation(
    relation_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> None:
    """Delete relation link."""
    try:
        await service.delete_relation(relation_id, owner_id="default_owner", soft_delete=True)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


# --- COLLECTIONS ---

@router.post("/collections", response_model=KnowledgeCollectionResponse, status_code=201)
async def create_collection(
    req: CreateCollectionRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeCollectionResponse:
    """Create a new collection container."""
    try:
        metadata = KnowledgeMetadata(tags=req.tags, custom_metadata=req.custom_metadata)
        col = await service.create_collection(
            owner_id="default_owner",
            name=req.name,
            description=req.description,
            metadata=metadata,
        )
        return KnowledgeCollectionResponse.from_domain(col)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get("/collections", response_model=KnowledgeListResponse[KnowledgeCollectionResponse])
async def list_collections(
    status: KnowledgeStatus | None = Query(default=KnowledgeStatus.ACTIVE),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeListResponse[KnowledgeCollectionResponse]:
    """List collections belonging to owner."""
    try:
        collections, total = await service.list_collections(
            owner_id="default_owner", status=status, page=page, page_size=page_size
        )
        return KnowledgeListResponse(
            items=[KnowledgeCollectionResponse.from_domain(c) for c in collections],
            total=total,
            page=page,
            page_size=page_size,
        )
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get("/collections/{collection_id}", response_model=KnowledgeCollectionResponse)
async def get_collection(
    collection_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeCollectionResponse:
    """Get collection details by ID."""
    try:
        col = await service.get_collection(collection_id, owner_id="default_owner")
        return KnowledgeCollectionResponse.from_domain(col)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.patch("/collections/{collection_id}", response_model=KnowledgeCollectionResponse)
async def update_collection(
    collection_id: str,
    req: UpdateCollectionRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeCollectionResponse:
    """Update collection properties."""
    try:
        metadata = (
            KnowledgeMetadata(tags=req.tags or [], custom_metadata=req.custom_metadata or {})
            if (req.tags is not None or req.custom_metadata is not None)
            else None
        )
        updated = await service.update_collection(
            collection_id=collection_id,
            owner_id="default_owner",
            name=req.name,
            description=req.description,
            metadata=metadata,
        )
        return KnowledgeCollectionResponse.from_domain(updated)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.delete("/collections/{collection_id}", status_code=204)
async def delete_collection(
    collection_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> None:
    """Delete collection."""
    try:
        await service.delete_collection(collection_id, owner_id="default_owner", soft_delete=True)
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


# --- SEARCH ---

@router.post("/search", response_model=KnowledgeListResponse[KnowledgeEntityResponse])
async def search_knowledge(
    req: KnowledgeSearchRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeListResponse[KnowledgeEntityResponse]:
    """Execute deterministic search across knowledge entities."""
    try:
        filter_spec = KnowledgeSearchFilter(
            owner_id="default_owner",
            query=req.query,
            entity_type=req.entity_type,
            status=req.status,
            confidence=req.confidence,
            collection_id=req.collection_id,
            tags=req.tags,
            source_type=req.source_type,
            page=req.page,
            page_size=req.page_size,
        )
        entities, total = await service.search_entities(filter_spec)
        return KnowledgeListResponse(
            items=[KnowledgeEntityResponse.from_domain(e) for e in entities],
            total=total,
            page=req.page,
            page_size=req.page_size,
        )
    except KnowledgeError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc

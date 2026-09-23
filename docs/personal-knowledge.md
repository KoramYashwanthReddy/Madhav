# Module 09 — Personal Knowledge Engine

## Architecture & System Overview

The **Personal Knowledge Engine** organizes persistent, structured knowledge that belongs to the user and represents their real-world environment, domain relationships, facts, and collections.

```
User
 ↓
Interface
 ↓
AI Runtime
 ↓
Context (Module 06)
 ↓
Memory (Module 08)
 ↓
Personal Knowledge (Module 09)
 ↓
[Future Modules: RAG, Reasoning, Agents]
```

### Key Distinction: Memory vs Personal Knowledge

- **Memory (Module 08)** answers: *"What raw statement or experience did the user communicate?"*
  - Example: *"The user said yesterday that they are learning Spring Boot."*
- **Personal Knowledge (Module 09)** answers: *"What structured knowledge does Madhav maintain about the user and their world?"*
  - Example: Entity `Spring Boot` (type: `TECHNOLOGY`), Relation `User -> LEARNING -> Spring Boot`, with provenance referencing `memory_id`.

---

## Knowledge Domain Model

### 1. Knowledge Entity (`KnowledgeEntity`)
Persistent real-world or conceptual object.
- **Entity Types (`KnowledgeEntityType`)**: `PERSON`, `PROJECT`, `ORGANIZATION`, `COMPANY`, `SKILL`, `TECHNOLOGY`, `GOAL`, `INTEREST`, `EDUCATION`, `JOB`, `LOCATION`, `DOCUMENT`, `CONCEPT`, `EVENT`, `OTHER`.
- **Fields**: `id`, `owner_id`, `type`, `name`, `description`, `status`, `confidence`, `scope`, `collection_id`, `metadata`, `created_at`, `updated_at`, `archived_at`, `deleted_at`.

### 2. Knowledge Fact (`KnowledgeFact`)
Structured statement assertion about an entity.
- **Value Types (`FactValueType`)**: `TEXT`, `NUMBER`, `BOOLEAN`, `DATE`, `DATETIME`, `REFERENCE`, `JSON`.
- **Temporal Validity**: Supports `valid_from` and `valid_until` timestamps.
- **Fields**: `id`, `owner_id`, `entity_id`, `subject`, `predicate`, `object`, `value`, `value_type`, `confidence`, `source_type`, `source_reference`, `status`, `valid_from`, `valid_until`, `created_at`, `updated_at`.

### 3. Knowledge Relation (`KnowledgeRelation`)
Explicit directed relationships between entities.
- **Relation Types (`KnowledgeRelationType`)**: `OWNS`, `USES`, `WORKS_ON`, `WORKS_AT`, `LEARNED`, `LEARNING`, `INTERESTED_IN`, `PART_OF`, `RELATED_TO`, `DEPENDS_ON`, `CREATED`, `MANAGES`, `KNOWS`, `LOCATED_AT`, `HAS_SKILL`, `HAS_GOAL`, `HAS_EXPERIENCE`.
- **Fields**: `id`, `owner_id`, `source_entity_id`, `relation_type`, `target_entity_id`, `confidence`, `source_type`, `source_reference`, `metadata`, `status`, `created_at`, `updated_at`.

### 4. Knowledge Collection (`KnowledgeCollection`)
Organizational structures grouping related entities (e.g., *Personal*, *Career*, *Education*, *Projects*, *Technology*, *Goals*, *Interests*).

### 5. Knowledge Version (`KnowledgeVersion`)
Monotonically increasing historic snapshots created automatically whenever an entity or fact is created or modified.

### 6. Provenance & Memory Integration
Every knowledge assertion records its source provenance:
- **Source Types**: `USER_EXPLICIT`, `USER_PROFILE`, `CONVERSATION`, `MEMORY`, `IMPORTED`, `MANUAL`, `SYSTEM`, `FUTURE_AI_INFERENCE`.
- **Source Reference**: Contains origin pointers such as `memory_id`, `conversation_id`, or `message_id`.

---

## Context Management Integration

`PersonalKnowledgeContextSource` integrates cleanly with Module 06 `ContextManager`:
- Exposes active knowledge entities, facts, and aggregated summaries as `ContextItem` instances under `category=KNOWLEDGE`.
- Honors context token budgets, required item flags, and owner boundaries.

---

## API Layer

REST endpoints available under `/api/v1/knowledge`:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/knowledge/entities` | Create Knowledge Entity |
| `GET` | `/api/v1/knowledge/entities` | List entities with query and status filters |
| `GET` | `/api/v1/knowledge/entities/{entity_id}` | Retrieve entity by ID |
| `PATCH` | `/api/v1/knowledge/entities/{entity_id}` | Update entity properties |
| `DELETE` | `/api/v1/knowledge/entities/{entity_id}` | Soft delete entity |
| `POST` | `/api/v1/knowledge/entities/{entity_id}/archive` | Archive entity |
| `POST` | `/api/v1/knowledge/entities/{entity_id}/restore` | Restore entity |
| `GET` | `/api/v1/knowledge/entities/{entity_id}/summary` | Get aggregated entity summary projection |
| `GET` | `/api/v1/knowledge/entities/{entity_id}/facts` | List facts for an entity |
| `GET` | `/api/v1/knowledge/entities/{entity_id}/relations` | List incoming/outgoing relations |
| `POST` | `/api/v1/knowledge/facts` | Create Knowledge Fact assertion |
| `GET` | `/api/v1/knowledge/facts/{fact_id}` | Get fact details |
| `PATCH` | `/api/v1/knowledge/facts/{fact_id}` | Update fact assertion |
| `DELETE` | `/api/v1/knowledge/facts/{fact_id}` | Soft delete fact |
| `POST` | `/api/v1/knowledge/relations` | Create relation link |
| `GET` | `/api/v1/knowledge/relations/{relation_id}` | Get relation details |
| `DELETE` | `/api/v1/knowledge/relations/{relation_id}` | Soft delete relation |
| `POST` | `/api/v1/knowledge/collections` | Create collection |
| `GET` | `/api/v1/knowledge/collections` | List collections |
| `GET` | `/api/v1/knowledge/collections/{collection_id}` | Get collection details |
| `PATCH` | `/api/v1/knowledge/collections/{collection_id}` | Update collection |
| `DELETE` | `/api/v1/knowledge/collections/{collection_id}` | Soft delete collection |
| `POST` | `/api/v1/knowledge/search` | Execute deterministic knowledge search |

---

## Architectural Boundaries

Module 09 strictly does **NOT** implement:
- RAG, vector databases, embeddings, or semantic search (Module 10)
- Automatic AI extraction or background autonomous learning loops
- Graph database engines, graph traversal algorithms, or visualizers
- LLM reasoning loops or agent engines (Modules 11-13)
- User interfaces or client applications

# Module 09 Architecture Reference — Personal Knowledge Engine

## Core Purpose

The **Personal Knowledge Engine** provides a structured, persistent knowledge representation of real-world entities, typed attributes, and directed graph relationships belonging to the user.

## Component Breakdown

1. **Domain Layer (`madhav.knowledge.domain`)**:
   - `KnowledgeEntity`: Persistent real-world/conceptual entity model.
   - `KnowledgeFact`: Typed property/attribute statement with temporal validity (`valid_from`, `valid_until`).
   - `KnowledgeRelation`: Directed edge connecting two entity nodes.
   - `KnowledgeCollection`: Organizational container grouping entities.
   - `KnowledgeVersion`: Version history snapshot tracking mutations.
   - `KnowledgeSummary`: Aggregate view of entity + facts + relations.

2. **Repository Layer (`madhav.knowledge.repositories`)**:
   - Repository protocols (`KnowledgeEntityRepository`, `KnowledgeFactRepository`, `KnowledgeRelationRepository`, `KnowledgeCollectionRepository`, `KnowledgeVersionRepository`).
   - `InMemoryKnowledgeRepository`: Thread-safe, lock-synchronized in-memory implementation supporting soft deletion and deterministic search.

3. **Service Layer (`madhav.knowledge.services`)**:
   - `KnowledgeDuplicateDetector`: Deterministic duplicate entity (owner + type + normalized name) and fact checking.
   - `KnowledgeService`: Application coordinator for CRUD, lifecycle state transitions, versioning, memory provenance, and privacy-safe logging.

4. **Context Source Layer (`madhav.knowledge.sources`)**:
   - `PersonalKnowledgeContextSource`: ContextSource adapter supplying `category=KNOWLEDGE` items to Module 06 `ContextManager`.

5. **API Layer (`madhav.knowledge.api`)**:
   - REST API router under `/api/v1/knowledge`.

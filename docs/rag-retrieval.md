# Module 10 — RAG & Retrieval Engine Documentation

## Overview

Max Module 10 provides the **Retrieval and RAG Infrastructure**. It is responsible for ingesting, normalizing, chunking, embedding, indexing, searching, and citing knowledge sources across the platform.

> [!IMPORTANT]
> **Architectural Boundary**: Module 10 is RETRIEVAL infrastructure.
> It does **NOT** implement:
> - Reasoning or planning (Module 11)
> - Autonomous agents or tasks (Modules 12–13)
> - Tool execution or computer control
> - Direct model answer generation
> - Web crawling or fine-tuning

---

## Key Features

1. **Document Model**: Multi-source document representation (`FILE`, `TEXT`, `URL`, `MEMORY`, `PERSONAL_KNOWLEDGE`, `MANUAL`, `IMPORT`) with explicit lifecycle state transitions (`ACTIVE`, `INDEXING`, `INDEXED`, `FAILED`, `ARCHIVED`, `DELETED`).
2. **Text Normalization**: Unicode NFKC normalization, standardized line breaks, and whitespace cleaning preserving semantic meaning.
3. **Deterministic Boundary-Aware Chunking**: Hierarchical paragraph -> sentence -> word boundary splitting with configurable target size (`chunk_size`), overlap (`chunk_overlap`), and character start/end tracking. Zero LLM dependencies.
4. **Idempotency via Content Hashing**: SHA-256 hash tracking prevents duplicate chunking and vector storage for identical document content.
5. **Embedding Abstraction**: `EmbeddingProvider` interface with unit-tested `DevelopmentEmbeddingProvider` (deterministic 64-dimensional hash vectors) for offline execution.
6. **Vector Store Abstraction**: `VectorStore` interface with `InMemoryVectorStore` supporting top-k cosine similarity, metadata filtering, owner isolation, and deterministic tie-breaking (score descending, chunk_id ascending).
7. **Module 06 Context Integration**: `RetrievalContextBuilder` maps search results into Module 06 `ContextItem` objects under `ContextCategory.KNOWLEDGE`, enforcing context character and token budgets.
8. **Module 08 & 09 Adapters**: `MemoryRAGAdapter` and `KnowledgeRAGAdapter` for explicit provenance-aware indexing of memories and knowledge entities/facts.
9. **Citations & Provenance**: Every retrieved chunk preserves provenance details (source type, reference ID, document title, paragraph location, relevance score).
10. **REST APIs**: Full OpenAPI endpoints under `/api/v1/rag` for document management, search queries, and health status reporting.

---

## Architecture & Flow

```
[Knowledge / Text Source / File / Memory]
                 │
                 ▼
          Text Normalizer (NFKC, LF)
                 │
                 ▼
         SHA-256 Content Hash
                 │
                 ▼
       Boundary-Aware Chunker
                 │
                 ▼
         Embedding Provider
                 │
                 ▼
           Vector Store
                 │
                 ▼
        Similarity Search & Filter
                 │
                 ▼
     Retrieval Context Builder
                 │
                 ▼
     Module 06 ContextManager
```

---

## Configuration

Subsystem parameters are configured in `MAX_RAG__*` environment variables or settings:

| Parameter | Default | Description |
|---|---|---|
| `enabled` | `true` | Toggle RAG subsystem |
| `chunk_size` | `512` | Target chunk character count |
| `chunk_overlap` | `64` | Overlap character count between chunks |
| `minimum_chunk_size` | `32` | Minimum character size boundary |
| `maximum_chunk_size` | `2048` | Maximum character size boundary |
| `default_top_k` | `5` | Default number of vector results |
| `max_top_k` | `50` | Maximum top_k limit |
| `minimum_score` | `0.0` | Default relevance threshold |
| `embedding_provider` | `development` | Active embedding provider |
| `embedding_dimensions` | `64` | Output vector dimension size |
| `vector_store_provider` | `memory` | Active vector store backend |

---

## API Endpoints

- `POST /api/v1/rag/documents` — Ingest and index a document
- `GET /api/v1/rag/documents` — List owner documents
- `GET /api/v1/rag/documents/{id}` — Get document details
- `PATCH /api/v1/rag/documents/{id}` — Update & reindex document
- `DELETE /api/v1/rag/documents/{id}` — Delete document & purge vectors
- `POST /api/v1/rag/documents/{id}/index` — Trigger indexing
- `POST /api/v1/rag/documents/{id}/reindex` — Trigger reindexing
- `POST /api/v1/rag/search` — Perform vector search with filters
- `POST /api/v1/rag/retrieve` — Alias for search
- `GET /api/v1/rag/status` — Subsystem health metrics

---

## Current Limitations

- Development embedding provider uses deterministic pseudorandom hash vectors intended for offline testing. Real embedding models (e.g. sentence-transformers or local models) will plug into `EmbeddingProvider`.
- Default vector store is in-memory (`InMemoryVectorStore`). Production scale-out to pgvector can be attached via `VectorStore` interface.

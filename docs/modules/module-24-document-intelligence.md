# Module 24 — Document Intelligence

> **Status**: Production-Ready  
> **Module**: 24 of Max Personal AI  
> **Layer**: Infrastructure → Intelligence  
> **Author**: Max Architecture Team

---

## 1. Responsibility & Scope

Module 24 provides structured **understanding** of documents. It is the bridge between raw file bytes and structured, reasoned information that higher-level modules (reasoning, agents, RAG, tools) can consume.

### What Module 24 IS

| Capability | Description |
|---|---|
| **Multi-format parsing** | PDF, DOCX, XLSX, PPTX, TXT, MD, CSV, JSON, XML |
| **Metadata extraction** | Author, title, creation date, word count, page count |
| **Structure normalization** | Headings, sections, paragraphs, tables, lists, slides, sheets |
| **Security enforcement** | Prompt injection defense, XXE protection, size limits |
| **Deterministic search** | Exact-text matching with citation provenance |
| **Document comparison** | Machine-readable unified diff between two documents |
| **Version management** | Content-hash-based snapshot history |
| **RAG preparation** | Structured chunk candidates for M10 (RAG Engine) |
| **Generation** | Create new TXT/MD documents from structured Markdown |
| **Conversion** | Convert documents between supported formats |
| **Audit trail** | Full operation log per document |

### What Module 24 is NOT

| NOT responsible for | Correct module |
|---|---|
| Filesystem management / file browser | Module 17 (FilesystemService) |
| Semantic vector search / embeddings | Module 10 (RAG Engine) |
| AI reasoning over documents | Module 11 (Reasoning) |
| Image/OCR recognition | Module 25 (Vision) — future |
| Web scraping / fetch | Module 13 (Web Intelligence) |
| Code analysis | Module 22 (Coding Agent) |
| Terminal execution | Module 21 (Terminal) |

---

## 2. Architecture

```
Document Source (file path / reference)
         │
         ▼
DocumentFilesystemAdapter ──── routes via M17 FilesystemService
         │
         ▼
DocumentParserRegistry ──── detect format (extension + MIME + magic bytes)
         │
         ▼
Concrete Parser (TXT / MD / CSV / JSON / XML / PDF / DOCX / XLSX / PPTX)
         │
         ▼
DocumentSecurityEnforcer ──── prompt injection scan + XXE defense
         │
         ▼
DocumentService ──── orchestrates registration, processing, search, compare
         │
    ┌────┼──────┬───────────┐
    │    │      │           │
    ▼    ▼      ▼           ▼
DocRepo VerRepo JobRepo AuditRepo  (in-memory, replaceable)
         │
         ▼
DocumentRAGAdapter ──── chunk prep → M10 (RAG Engine)
         │
API Routes (/api/v1/documents/*)
```

### Layer Map

| Layer | Package | Key Classes |
|---|---|---|
| Domain | `document/domain/` | `Document`, `DocumentMetadata`, `DocumentStructure`, enums, exceptions |
| Parsers | `document/parsers/` | `DocumentParserRegistry`, `BaseDocumentParser`, 9 concrete parsers |
| Security | `document/security/` | `DocumentSecurityEnforcer` |
| Adapters | `document/adapters/` | `DocumentFilesystemAdapter`, `DocumentRAGAdapter` |
| Generators | `document/generators/` | `BaseDocumentGenerator` |
| Converters | `document/converters/` | `BaseDocumentConverter` |
| Repositories | `document/repositories/` | `DocumentRepository`, `DocumentVersionRepository`, `DocumentProcessingRepository`, `DocumentAuditRepository` |
| Services | `document/services/` | `DocumentService`, `register_document_tools` |
| Container | `document/container.py` | `DocumentContainer`, `get_document_container()` |
| API | `document/api/routes.py` | FastAPI router — 20 endpoints |

---

## 3. Security Architecture

> **Core Principle**: Documents are **UNTRUSTED DATA**. Every byte from an external document is treated as potentially hostile.

### 3.1 Prompt Injection Defense

`DocumentSecurityEnforcer` scans all extracted text for known injection patterns before any text is returned or stored:

- `"ignore all previous instructions"`
- `"you are now [DAN/jailbreak]"`
- `"SYSTEM: new directive"`
- Hundreds of similar injection vectors (extensible via config)

All extracted text is **wrapped in UNTRUSTED DATA boundaries** regardless:

```
--- UNTRUSTED DOCUMENT CONTENT START ---
[document text here]
--- UNTRUSTED DOCUMENT CONTENT END ---
```

### 3.2 XXE Protection

The XML parser explicitly disables entity expansion and DTD loading to prevent Server-Side Request Forgery (SSRF) and local file disclosure via XXE.

### 3.3 Decompression Bomb Protection

All parsers enforce the global `max_file_size_mb` limit (default: 25 MB) **before** decompression. DOCX/XLSX/PPTX (ZIP-based) enforce member file size limits.

### 3.4 Path Traversal Prevention

All file access routes through `DocumentFilesystemAdapter` → `FilesystemService` (M17) which enforces path sandboxing via the existing Permission Gate (M15).

### 3.5 Content Hash Integrity

Every registered document stores a SHA-256 hash of raw bytes. Deduplication is hash-based, preventing duplicate processing of identical content.

---

## 4. Format Support Matrix

| Format | Extension | Parser | Metadata | Structure | Tables | Notes |
|---|---|---|---|---|---|---|
| Plain Text | `.txt` | `TextParser` | ✅ | Paragraphs | ❌ | Encoding detection |
| Markdown | `.md` | `MarkdownParser` | ✅ | Headings, sections, lists | ✅ | H1-H6 hierarchy |
| CSV | `.csv` | `CSVParser` | ✅ | Table | ✅ | Header detection |
| JSON | `.json` | `JSONParser` | ✅ | Key-value tree | ❌ | Invalid JSON → warning |
| XML | `.xml` | `XMLParser` | ✅ | Element tree | ❌ | XXE blocked |
| PDF | `.pdf` | `PDFParser` | ✅ | Pages | ✅ | Requires `pypdf` |
| Word | `.docx` | `DocxParser` | ✅ | Headings, paragraphs, lists, tables | ✅ | Requires `python-docx` |
| Excel | `.xlsx` | `XLSXParser` | ✅ | Sheets, tables | ✅ | Requires `openpyxl` |
| PowerPoint | `.pptx` | `PPTXParser` | ✅ | Slides | ✅ | Requires `python-pptx` |

---

## 5. API Reference

All endpoints are prefixed `/api/v1/documents`.

### Registration & Processing

| Method | Path | Description |
|---|---|---|
| `POST` | `/register` | Register document by path/reference |
| `POST` | `/{document_id}/process` | Parse, extract structure + metadata |

### Retrieval

| Method | Path | Description |
|---|---|---|
| `GET` | `` | List all documents |
| `GET` | `/{document_id}` | Get document entity |
| `GET` | `/{document_id}/metadata` | Get extracted metadata |
| `GET` | `/{document_id}/content` | Get full extracted text |
| `GET` | `/{document_id}/structure` | Get normalized structure |
| `GET` | `/{document_id}/summary` | Get compact summary |
| `DELETE` | `/{document_id}` | Delete document |

### Versions

| Method | Path | Description |
|---|---|---|
| `GET` | `/{document_id}/versions` | List version history |
| `GET` | `/versions/{version_id}` | Get specific version |

### Validation, Search & Comparison

| Method | Path | Description |
|---|---|---|
| `GET` | `/{document_id}/validate` | Run integrity + security checks |
| `POST` | `/search` | Exact-text search with citations |
| `POST` | `/compare` | Diff two documents |

### RAG Integration

| Method | Path | Description |
|---|---|---|
| `POST` | `/{document_id}/rag/prepare` | Prepare RAG chunks for M10 |

### Generation & Conversion

| Method | Path | Description |
|---|---|---|
| `POST` | `/generate` | Generate new document from Markdown |
| `POST` | `/convert` | Convert document to target format |

### System

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Subsystem health status |

---

## 6. Module Integration Map

| Integrated Module | Integration Point | Direction |
|---|---|---|
| M10 — RAG Engine | `DocumentRAGAdapter.prepare_rag_chunks()` | M24 → M10 |
| M14 — Tool Registry | `register_document_tools()` | M24 → M14 |
| M15 — Permission Gate | `DocumentSecurityEnforcer.check_permission()` | M24 → M15 |
| M17 — FilesystemService | `DocumentFilesystemAdapter` routes all file I/O | M24 → M17 |

---

## 7. Configuration

Configured via `DocumentSettings` in `config/sections.py`:

```python
class DocumentSettings(BaseModel):
    enabled: bool = True
    max_file_size_mb: int = 25
    supported_formats: list[str] = ["pdf", "docx", "xlsx", "pptx", "txt", "md", "csv", "json", "xml"]
    enable_prompt_injection_defense: bool = True
    enable_xxe_protection: bool = True
    max_pages_per_document: int = 500
    max_elements_per_document: int = 10000
```

Environment variables (`.env`):
```
DOCUMENT__ENABLED=true
DOCUMENT__MAX_FILE_SIZE_MB=25
DOCUMENT__ENABLE_PROMPT_INJECTION_DEFENSE=true
```

---

## 8. Usage Examples

### Register and Process a Document

```python
from max.document import get_document_container

container = get_document_container()
service = container.service

# Step 1: Register
doc = await service.register_document(
    source_reference="/data/reports/q4_report.pdf",
    filename="q4_report.pdf",
    source_type=DocumentSource.LOCAL_FILE,
    owner_id="user_001",
)

# Step 2: Process
result = await service.process_document(doc.id)

print(result.raw_text[:500])  # Security-wrapped extracted text
print(result.metadata.page_count)  # 42
print(result.structure.tables)  # List[DocumentTable]
```

### Search Across Documents

```python
from max.document.domain.models import DocumentSearchRequest

req = DocumentSearchRequest(
    query="quarterly revenue",
    case_sensitive=False,
    max_results=10,
)
response = service.search_documents(req)
for match in response.results:
    print(f"[{match.filename}] {match.citation.formatted_citation}")
    print(f"  Context: {match.context}")
```

### Compare Two Documents

```python
comparison = service.compare_documents(doc_v1.id, doc_v2.id)
print(f"Changes: +{comparison.added_count} -{comparison.removed_count} ~{comparison.modified_count}")
for change in comparison.changes:
    print(f"  [{change.change_type.value}] at {change.location}")
```

### Prepare RAG Chunks

```python
chunks = service.prepare_rag(doc.id)
# Pass to M10 RAG Engine for embedding + indexing
for chunk in chunks:
    print(chunk["text"], chunk["metadata"])
```

---

## 9. Dependencies

### Python Package Requirements

```toml
# pyproject.toml — optional extras (gracefully degraded if absent)
[project.optional-dependencies]
document = [
    "pypdf>=4.0.0",           # PDF parsing
    "python-docx>=1.1.0",     # DOCX parsing
    "openpyxl>=3.1.0",        # XLSX parsing
    "python-pptx>=0.6.21",    # PPTX parsing
]
```

> All optional dependencies are gracefully handled. If `pypdf` is absent, the PDF parser emits a structured warning and returns the raw bytes as fallback text.

---

## 10. Testing

```bash
# Run Module 24 tests only
pytest tests/unit/test_document_intelligence.py -v

# Run full suite
pytest tests/ -v

# With coverage
pytest tests/unit/test_document_intelligence.py -v --cov=src/max/document --cov-report=term-missing
```

### Test Coverage Areas

| Area | Test Class |
|---|---|
| Domain enums | `TestDocumentEnums` |
| Domain models | `TestDocumentModels` |
| Parser registry (format detection) | `TestDocumentParserRegistry` |
| Text & Markdown parsers | `TestTextParser` |
| JSON parser (including invalid JSON) | `TestJSONParser` |
| CSV parser | `TestCSVParser` |
| XML parser (including XXE defense) | `TestXMLParser` |
| Prompt injection defense | `TestDocumentSecurityEnforcer` |
| In-memory repositories | `TestDocumentRepository` |
| Service registration + deduplication | `TestDocumentServiceRegistration` |
| Service search | `TestDocumentServiceSearch` |
| Service comparison (diff) | `TestDocumentServiceComparison` |
| Service validation + summary | `TestDocumentServiceValidation` |
| Tool registration | `TestDocumentToolRegistration` |
| DI container + singleton | `TestDocumentContainer` |
| REST API (all endpoints) | `TestDocumentAPI` |

---

## 11. File Structure

```
src/max/document/
├── __init__.py                    # Module public API surface
├── container.py                   # DI container + get_document_container()
├── adapters/
│   ├── __init__.py
│   ├── filesystem_adapter.py      # Routes I/O through M17
│   └── rag_adapter.py             # Chunk prep for M10
├── api/
│   ├── __init__.py
│   └── routes.py                  # 20 FastAPI endpoints
├── converters/
│   ├── __init__.py
│   └── base.py                    # BaseDocumentConverter
├── domain/
│   ├── __init__.py
│   ├── enums.py                   # DocumentFormat, DocumentType, etc.
│   ├── exceptions.py              # DocumentError hierarchy
│   └── models.py                  # All Pydantic domain models
├── generators/
│   ├── __init__.py
│   └── base.py                    # BaseDocumentGenerator
├── parsers/
│   ├── __init__.py
│   ├── base.py                    # BaseDocumentParser ABC
│   ├── registry.py                # DocumentParserRegistry
│   ├── text_parser.py
│   ├── markdown_parser.py
│   ├── csv_parser.py
│   ├── json_parser.py
│   ├── xml_parser.py
│   ├── pdf_parser.py
│   ├── docx_parser.py
│   ├── xlsx_parser.py
│   └── pptx_parser.py
├── repositories/
│   ├── __init__.py
│   └── repositories.py            # 4 in-memory repositories
└── security/
    ├── __init__.py
    └── prompt_injection.py        # DocumentSecurityEnforcer

tests/unit/
└── test_document_intelligence.py  # 60+ unit + integration tests

docs/modules/
└── module-24-document-intelligence.md  # This file
```

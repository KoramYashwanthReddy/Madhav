# Madhav: Personal AI Assistant System Architecture

## 1. What Madhav Is
**Madhav** is a modular, high-performance personal AI system designed to operate locally with deep system integration, persistent memory, multimodal intelligence, and safe autonomous task execution capabilities. 

---

## 2. Project Vision
The long-term vision of Madhav is to become a fully capable, secure personal AI companion and operating agent. Key target capabilities include:
- **Natural Conversation & Multimodal Reasoning**: Voice, text, and visual context understanding.
- **Reasoning & Planning**: Multi-step goal decomposition and structured execution.
- **Persistent Memory & PKM**: Long-term contextual memory, document knowledge retrieval (RAG), and personal knowledge management.
- **Controlled System & Computer Interaction**: Safe execution of filesystem operations, terminal processes, browser automation, and desktop app interactions.
- **Privacy-First & Local-First**: Core execution powered by locally managed open-weights models and secure local data stores.

---

## 3. Architecture Direction
Madhav follows a modular micro-component architecture designed for scalability, safety, and strict separation of concerns:

```
Madhav/
├── apps/               # Frontend applications (React/Vite/Desktop)
├── backend/            # FastAPI core service & API management
├── ai/                 # Inference engines, memory, orchestration, & agent logic
├── system-agent/       # OS control layers (FS, process, terminal, screen, security)
├── knowledge/          # Vector indexes, RAG engines, knowledge graphs
├── models/             # Local model storage, checkpoints, fine-tuned adapters
├── database/           # Relational schema migrations and seed scripts
├── infrastructure/     # Container orchestrations (Docker Compose, MinIO, Redis, Postgres)
├── tests/              # Automated unit, integration, and end-to-end evaluation suites
├── scripts/            # Build, setup, and deployment automation scripts
└── docs/               # System specifications and architectural design documents
```

### Core Design Rules
1. **Python Primary**: Core backend services, AI runtime, and orchestration logic are built in Python 3.12+.
2. **Rust for Low-Level Operations**: Rust is reserved for system-level binaries where security sandboxing, performance, or deep OS API bindings are needed.
3. **Controlled Execution Sandboxing**: LLMs never execute arbitrary shell commands directly. All action proposals pass through a permission gate and audit logger.
4. **Framework Minimalism**: Built on clean, lightweight foundations without bloat frameworks.

---

## 4. Technology Stack

| Domain | Selected Technologies |
| :--- | :--- |
| **Core Runtime** | Python 3.12+, Rust (System Extensions) |
| **Backend & API** | FastAPI, Pydantic v2, Uvicorn |
| **AI & Training** | PyTorch, Hugging Face (Transformers, Datasets, Tokenizers, PEFT, TRL, Accelerate) |
| **Local Inference** | llama.cpp, vLLM |
| **Database & Cache** | PostgreSQL + pgvector, Redis, MinIO (Object Storage) |
| **Speech & Vision** | Whisper-family models, Piper TTS, OpenCV, OCR, Vision-Language Models |
| **System Automation** | Playwright (Browser Automation), Native OS APIs |
| **Frontend & GUI** | React, TypeScript, Vite, Tauri (Desktop packaging) |
| **Containerization** | Docker, Docker Compose |
| **Testing & Observability** | Pytest, Playwright, OpenTelemetry, Structured JSON Logging |

---

## 5. Current Development Phase
**Phase 1: Foundation & Core Scaffold**
- Clean repository structure established.
- Core FastAPI server initialized with `/health` verification endpoint.
- Unit testing framework setup with Pytest.
- Zero mock implementations or placeholder runtime code.

---

## 6. Security Philosophy
Madhav is designed with defense-in-depth security principles:
1. **Zero Unchecked Execution**: Model outputs are strictly structured schemas (Pydantic / JSON Schema).
2. **Permission Gate & Tool Registry**: Every system mutation (filesystem, process execution, screen grab, network request) requires explicit authorization policies.
3. **Isolation & Least Privilege**: Dangerous tools operate inside isolated sandboxes (containers/jail cells).
4. **Audit Logging**: Every action proposal, policy check, user confirmation, and execution result is logged deterministically.

---

## 7. Development Setup

### Prerequisites
- Python 3.12+
- Git

### Initializing Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install editable package with dev dependencies
pip install -e ".[dev]"
```

### Running the API Server
```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 8. Testing Approach

### Running Automated Tests
```bash
pytest
```

Current test suite validates basic server initialization and health endpoint status.

---

## 9. Future Roadmap
1. **Phase 2: Local AI Runtime & Inference Engine** (llama.cpp / vLLM orchestration layer).
2. **Phase 3: Memory System & Knowledge Retrieval** (pgvector + Redis caching).
3. **Phase 4: Controlled System Tooling & Action Layer** (Security-sandboxed tool registry).
4. **Phase 5: Multimodal & Voice Pipeline** (Whisper + Piper TTS integration).
5. **Phase 6: Desktop User Interface** (Tauri + React dashboard).

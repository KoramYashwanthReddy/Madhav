# MADHAV

MADHAV is a long-term, production-quality personal AI system engineered for privacy, extensibility, testability, and multi-modal intelligence.

---

## What is MADHAV?

MADHAV is an autonomous personal AI platform designed to manage personal knowledge, reason across complex multi-step workflows, execute computer automation tasks, integrate with developer ecosystems, and adapt continuously to personal user profiles.

---

## Vision

The complete MADHAV architecture encompasses 41 distinct modules ranging from platform foundation and context management to computer control, proactive intelligence, and multi-modal autonomous systems. MADHAV aims to provide a secure, self-hosted, personal intelligence companion.

---

## Current Module

**Module 04 — AI Runtime**

This repository implements **Module 01: Platform Foundation**, **Module 02: Configuration & Environment**, **Module 03: Identity & Personal Profile**, and **Module 04: AI Runtime**. Future modules (05 to 41) are intentionally not implemented in this phase to maintain strict architectural boundaries and modular isolation.

---

## Architecture Philosophy

1. **Strict Modular Isolation**: Each module builds clean abstractions without early coupling to future features.
2. **Centralized Strongly Typed Settings**: All application modules consume runtime settings from `madhav.config` instead of directly accessing `os.getenv()`.
3. **Identity Decoupled from Authentication**: Identity defines *"Who Madhav is serving"* (`IdentityContext`) and operates independently from authentication mechanisms.
4. **Provider-Neutral AI Runtime**: Inference execution is decoupled from specific LLM vendors via `ModelRuntime` protocols and runtime registries, operating with an offline `StubModelRuntime` by default.
5. **Type Safety & Predictability**: Mandatory type annotations across all modules, verified via MyPy in strict mode.
6. **Structured & Secure Observability**: JSON-formatted logging with correlation IDs (`X-Request-ID`) and zero leakage of secret or personal credentials.
7. **Environment Independent & Testable**: Core logic operates deterministically without mandatory cloud dependencies, model weight downloads, or database state.

---

## Technology Stack

- **Language**: Python 3.12+
- **Package Manager**: `uv`
- **Configuration**: Pydantic Settings
- **Web Framework**: FastAPI & Uvicorn
- **Validation & Serialization**: Pydantic v2 & `pydantic-settings`
- **Testing**: Pytest, `pytest-asyncio`, `httpx`
- **Linting & Formatting**: Ruff
- **Type Checking**: MyPy

---

## Project Structure

```
Madhav/
├── src/
│   └── madhav/
│       ├── __init__.py
│       ├── main.py
│       ├── version.py
│       │
│       ├── ai/
│       │   ├── __init__.py
│       │   ├── exceptions.py
│       │   ├── api/
│       │   │   ├── __init__.py
│       │   │   └── routes.py
│       │   ├── domain/
│       │   │   ├── __init__.py
│       │   │   ├── capabilities.py
│       │   │   ├── enums.py
│       │   │   ├── execution.py
│       │   │   ├── messages.py
│       │   │   ├── parameters.py
│       │   │   ├── requests.py
│       │   │   ├── responses.py
│       │   │   └── usage.py
│       │   ├── runtime/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── manager.py
│       │   │   ├── registry.py
│       │   │   └── stub.py
│       │   └── schemas/
│       │       ├── __init__.py
│       │       ├── requests.py
│       │       └── responses.py
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   └── health.py
│       │
│       ├── config/
│       │   ├── __init__.py
│       │   ├── __main__.py
│       │   ├── enums.py
│       │   ├── errors.py
│       │   ├── loader.py
│       │   ├── sections.py
│       │   ├── settings.py
│       │   └── validators.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── application.py
│       │   ├── lifecycle.py
│       │   ├── exceptions.py
│       │   ├── error_handlers.py
│       │   ├── logging.py
│       │   ├── request_id.py
│       │   └── responses.py
│       │
│       ├── identity/
│       │   ├── __init__.py
│       │   ├── exceptions.py
│       │   ├── api/
│       │   │   └── routes.py
│       │   ├── domain/
│       │   │   └── ...
│       │   ├── repositories/
│       │   │   └── memory.py
│       │   ├── schemas/
│       │   │   └── ...
│       │   └── services/
│       │       └── identity_service.py
│       │
│       └── common/
│           ├── __init__.py
│           ├── types.py
│           └── interfaces.py
│
├── tests/
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_health.py
│   │   ├── test_exceptions.py
│   │   ├── test_logging.py
│   │   ├── test_request_id.py
│   │   ├── test_identity_domain.py
│   │   ├── test_identity_service.py
│   │   ├── test_ai_domain.py
│   │   └── test_ai_runtime.py
│   │
│   ├── integration/
│   │   ├── test_config_integration.py
│   │   ├── test_identity_api.py
│   │   ├── test_ai_api.py
│   │   └── test_application.py
│   │
│   └── conftest.py
│
├── docs/
│   └── architecture/
│       ├── module-01-platform-foundation.md
│       ├── module-02-configuration.md
│       ├── module-03-identity-personal-profile.md
│       └── module-04-ai-runtime.md
│
├── scripts/
│   ├── dev.py
│   └── verify.py
│
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## Configuration

MADHAV uses a centralized, strongly typed configuration system powered by `pydantic-settings`.

### Supported Environments
- `development` (Default): Local defaults, interactive docs (`/docs`, `/redoc`), hot reload support.
- `testing`: Isolated deterministic defaults, disables `.env` file inheritance.
- `production`: Enforces strict security validation rules (rejects `debug=True`, prohibits CORS origin wildcard `*` with credentials).

---

## Identity & Personal Profile

Module 03 introduces the identity domain contract and profile subsystem under `/api/v1/identity`:
- **Assistant Identity**: `GET /api/v1/identity/assistant` (Default name `"Madhav"`).
- **Owner Identity**: `GET /api/v1/identity/owner` (Partial profile support, zero fake personal data).
- **Personal Profile**: `GET /api/v1/identity/profile` & `PUT /api/v1/identity/profile`.
- **Safe Identity Summary**: `GET /api/v1/identity/summary` (Non-sensitive profile fields for safe logging).
- **Preferences**: `GET /api/v1/identity/preferences`, `PATCH /api/v1/identity/preferences`, `PATCH /api/v1/identity/communication`, `PATCH /api/v1/identity/locale`.
- **Profile Completeness**: `GET /api/v1/identity/completeness` (Deterministic score 0-100% and missing recommended fields).

---

## AI Runtime

Module 04 introduces provider-neutral AI inference execution under `/api/v1/ai`:
- **Generate AI Response**: `POST /api/v1/ai/generate`
- **Runtime Health Status**: `GET /api/v1/ai/runtime/status`
- **Runtime Capabilities**: `GET /api/v1/ai/runtime/capabilities`

---

## Development Setup

Install `uv` (if not already installed) and synchronize dependencies:

```bash
uv sync --extra dev
```

---

## Run

To start the local Uvicorn development server with hot reloading:

```bash
uv run python scripts/dev.py
```

---

## Test

To execute the unit and integration test suite:

```bash
uv run python -m pytest
```

---

## Lint

To check for code quality and style compliance using Ruff:

```bash
uv run python -m ruff check .
```

---

## Type Check

To verify static type safety with MyPy:

```bash
uv run python -m mypy src
```

---

## Platform Verification

To execute the full verification sequence (Configuration Diagnostics, Ruff, MyPy, Pytest):

```bash
uv run python scripts/verify.py
```

---

## Module Development Strategy

MADHAV is built sequentially across 41 modules:
- **01. Platform Foundation** [COMPLETED]
- **02. Configuration & Environment** [COMPLETED]
- **03. Identity & Personal Profile** [COMPLETED]
- **04. AI Runtime** [COMPLETED]
- 05. Model Management (Next)
- 06–41. (Future Modules)

Only Modules 01, 02, 03, and 04 are implemented in this repository state.


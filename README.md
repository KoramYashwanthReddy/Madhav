# MADHAV

MADHAV is a long-term, production-quality personal AI system engineered for privacy, extensibility, testability, and multi-modal intelligence.

---

## What is MADHAV?

MADHAV is an autonomous personal AI platform designed to manage personal knowledge, reason across complex multi-step workflows, execute computer automation tasks, integrate with developer ecosystems, and adapt continuously to personal user profiles.

---

## Vision

The complete MADHAV architecture encompasses 41 distinct modules ranging from platform foundation and context management to computer control, proactive intelligence, and multi-modal autonomous systems. MADHAV aims to provide a secure, self-hosted, personal intelligence companion.

---

## Current Status & Completed Modules

- **Module 01 — Platform Foundation** [COMPLETED]
- **Module 02 — Configuration & Environment** [COMPLETED]

Future modules (03 to 41) are intentionally not implemented in this phase to maintain strict architectural boundaries and modular isolation.

---

## Architecture Philosophy

1. **Single Source of Truth Configuration**: Centralized, strongly typed configuration (`pydantic-settings`). Direct `os.getenv()` calls across application modules are strictly prohibited.
2. **Strict Modular Isolation**: Each module builds clean abstractions without early coupling to future features.
3. **Type Safety & Predictability**: Mandatory type annotations across all modules, verified via MyPy in strict mode.
4. **Structured & Secure Observability**: JSON-formatted logging with correlation IDs (`X-Request-ID`) and zero leakage of secret credentials.
5. **Environment Independent & Testable**: Core logic operates deterministically without mandatory cloud dependencies or database state.

---

## Technology Stack

- **Language**: Python 3.12+
- **Package Manager**: `uv`
- **Configuration**: Pydantic Settings (`pydantic-settings`)
- **Web Framework**: FastAPI & Uvicorn
- **Validation & Serialization**: Pydantic v2
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
│       ├── config/
│       │   ├── __init__.py
│       │   ├── __main__.py       # CLI diagnostic inspector (python -m madhav.config)
│       │   ├── enums.py          # Environment & LogLevel
│       │   ├── errors.py         # Configuration exceptions
│       │   ├── loader.py         # Settings loader & caching
│       │   ├── sections.py       # Pydantic section models
│       │   └── settings.py       # Root Settings model & validation
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   └── health.py
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
│   │   └── test_request_id.py
│   │
│   ├── integration/
│   │   ├── test_application.py
│   │   └── test_config_fastapi.py
│   │
│   └── conftest.py
│
├── docs/
│   └── architecture/
│       ├── module-01-platform-foundation.md
│       └── module-02-configuration.md
│
├── scripts/
│   ├── dev.py
│   └── verify.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## Configuration & Environment Management

MADHAV uses a centralized Pydantic Settings architecture. All settings are loaded through `get_settings()`.

### Supported Environments

- `development`: Safe local defaults, auto-reloading enabled, interactive OpenAPI docs enabled.
- `testing`: Isolated, deterministic environment used during test suite execution. Local `.env` files are ignored to prevent test leakage.
- `production`: Strict security rules (debug mode forbidden, wildcard CORS origins forbidden with credentials, default secret key forbidden).

### Configuration Precedence

1. Safe built-in defaults (`sections.py`)
2. Environment-specific defaults
3. Local `.env` file (where allowed: development/local execution)
4. Environment variables prefixed with `MADHAV_` (e.g. `MADHAV_ENVIRONMENT`, `MADHAV_SERVER_PORT`, `MADHAV_LOG_LEVEL`)
5. Explicit runtime overrides

### Inspecting Configuration Diagnostics

To safely output redacted configuration diagnostics without exposing secrets:

```bash
uv run python -m madhav.config
```

---

## Development Setup

Install `uv` (if not already installed) and synchronize dependencies:

```bash
uv sync --extra dev
```

Copy `.env.example` to `.env` for local customization (never commit `.env`):

```bash
cp .env.example .env
```

---

## Run

To start the local Uvicorn development server with hot reloading:

```bash
uv run uvicorn madhav.main:app --reload
```

Alternatively, use the developer runner script:

```bash
uv run python scripts/dev.py
```

---

## Test

To execute the unit and integration test suite:

```bash
uv run pytest
```

---

## Lint & Format

To check for code quality and style compliance using Ruff:

```bash
uv run ruff check .
```

To automatically format files:

```bash
uv run ruff format .
```

---

## Type Check

To verify static type safety with MyPy:

```bash
uv run mypy src
```

---

## Foundation Verification

To execute the full verification sequence (Ruff, MyPy, Pytest):

```bash
uv run python scripts/verify.py
```

---

## Module Development Strategy

MADHAV is built sequentially across 41 modules:
- **01. Platform Foundation** [COMPLETED]
- **02. Configuration & Environment** [COMPLETED]
- 03. Identity & Personal Profile (Next)
- 04–41. (Future Modules)

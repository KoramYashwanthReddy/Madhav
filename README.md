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

**Module 02 — Configuration & Environment**

This repository implements **Module 01: Platform Foundation** and **Module 02: Configuration & Environment**. Future modules (03 to 41) are intentionally not implemented in this phase to maintain strict architectural boundaries and modular isolation.

---

## Architecture Philosophy

1. **Strict Modular Isolation**: Each module builds clean abstractions without early coupling to future features.
2. **Centralized Strongly Typed Settings**: All application modules consume runtime settings from `madhav.config` instead of directly accessing `os.getenv()`.
3. **Type Safety & Predictability**: Mandatory type annotations across all modules, verified via MyPy in strict mode.
4. **Structured & Secure Observability**: JSON-formatted logging with correlation IDs (`X-Request-ID`) and zero leakage of secret credentials.
5. **Environment Independent & Testable**: Core logic operates deterministically without mandatory cloud dependencies or database state.

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
│   │   ├── test_config_integration.py
│   │   └── test_application.py
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

### Environment Variable Precedence
1. Built-in defaults
2. Environment-specific defaults
3. `.env` file (loaded if present, ignored in `testing`)
4. Environment variables (prefixed with `MADHAV_`)
5. Explicit runtime overrides

### Environment Variable Naming
Environment variables use `MADHAV_` prefix and `__` (double underscore) for nested categories:

```bash
MADHAV_APPLICATION__ENVIRONMENT=development
MADHAV_APPLICATION__DEBUG=true
MADHAV_SERVER__HOST=127.0.0.1
MADHAV_SERVER__PORT=8000
MADHAV_LOGGING__LEVEL=INFO
MADHAV_SECURITY__SECRET_KEY=insecure-development-secret-key
```

### Configuration Diagnostics & Secret Masking
To inspect current active settings with secret fields masked:

```bash
uv run python -m madhav.config
```

Sample output:

```json
{
  "application": {
    "name": "MADHAV",
    "service": "madhav",
    "version": "0.1.0",
    "environment": "development",
    "debug": false
  },
  "server": {
    "host": "127.0.0.1",
    "port": 8000
  },
  "security": {
    "secret_key": "***REDACTED***"
  }
}
```

---

## Development Setup

Install `uv` (if not already installed) and synchronize dependencies:

```bash
uv sync --extra dev
```

Copy `.env.example` to `.env` for local configuration overrides:

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
uv run python -m pytest
```

---

## Lint

To check for code quality and style compliance using Ruff:

```bash
uv run python -m ruff check .
```

To automatically format files:

```bash
uv run python -m ruff format --check .
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

## Architecture Rules

- **Centralized Settings Access**: Application code must consume settings via `get_settings()` from `madhav.config` instead of reading `os.getenv()` directly.
- **No Mocking Future Modules**: Module 02 provides configuration foundations without creating fake or stubbed implementations of future AI components.
- **Secret Redaction**: Secret values use `SecretStr` and are masked (`***REDACTED***`) in logs, diagnostic dumps, and API responses.
- **Zero Raw Stack Traces**: Internal exceptions are caught and logged with tracebacks while returning sanitized error envelopes to clients.

---

## Security Philosophy

- Automatic header masking for Authorization/Bearer tokens and password strings in log outputs.
- Header validation for incoming `X-Request-ID` to prevent header injection.
- Strict production configuration validation rejecting dangerous settings (e.g. `debug=True` in production).

---

## Module Development Strategy

MADHAV is built sequentially across 41 modules:
- **01. Platform Foundation** [COMPLETED]
- **02. Configuration & Environment** [COMPLETED]
- 03. Identity & Personal Profile (Next)
- 04–41. (Future Modules)

Only Modules 01 and 02 are implemented in this repository state.

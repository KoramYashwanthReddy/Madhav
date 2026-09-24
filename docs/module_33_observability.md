# Module 33 — Observability & Audit

## Purpose & Overview

Module 33 provides a production-grade, OpenTelemetry-compatible **Observability & Audit System** for the MAX personal AI runtime. It allows developers, operators, and security systems to systematically answer:

- **"What happened?"** (Structured Logs & Audit Events)
- **"When did it happen?"** (Timestamps & Relative Execution Timelines)
- **"Which component did it?"** (Service & Component Metadata)
- **"Why did it happen?"** (Context Correlation & Cause References)
- **"What tools & permissions were involved?"** (Trace Spans & Audit Records)
- **"How long did it take?"** (Latency & Duration Metrics)
- **"What failed?"** (Error Records & Stack Trace References)

---

## Critical Architectural Principle

> **Module 33 OBSERVES MAX. It does NOT control MAX.**

Module 33 MUST NOT:
- Execute tools
- Modify permissions or bypass Module 15 security rules
- Change user preferences or memory
- Alter security policies or restart arbitrary services
- Browse websites or send external notifications

Module 33 strictly records events, measures latency, propagates correlation context, and exposes structured APIs for observation.

---

## Observability Signals

The system maintains 4 distinct, conceptually separated telemetry signals:

1. **LOGS**: Structured JSON entries describing individual operational messages or events (`TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
2. **METRICS**: Bounded numerical system measurements (`Counter`, `Gauge`, `Histogram`, `Timer`, `Rate`).
3. **TRACES**: Parent-child execution span flow across HTTP requests, AI models, agents, tools, memory, RAG, and scheduler automations.
4. **AUDIT EVENTS**: Durable, append-only security and business records (`PERMISSION_DENIED`, `INTEGRATION_CONNECTED`, `AUTOMATION_EXECUTED`, etc.).

---

## Core Identifiers & Context Propagation

Every execution context automatically carries strongly-typed correlation identifiers via Python `contextvars` (`ObservabilityContext`):

- `request_id`: Identifies single HTTP API invocations.
- `correlation_id`: Links multi-step workflows (Conversation → Task → Agent → Tool → Integration).
- `trace_id`: OpenTelemetry trace identifier.
- `span_id`: Unique identifier for an individual execution span.
- `execution_id`: Identifier for end-to-end task/agent run executions.

---

## Secret Redaction & AI Content Privacy

### Centralized Secret Redaction
All log messages, span attributes, tool input arguments, output payloads, and audit details pass through `RedactionService`. Automatically masks sensitive parameters including:
`password`, `api_key`, `access_token`, `refresh_token`, `jwt`, `cookie`, `authorization`, `private_key`, `client_secret`, `db_password`, etc.

### Prompt & Response Privacy
Raw AI prompts and completions are NOT logged by default in production. The system stores SHA-256 content hashes and truncated redacted previews unless explicit opt-in capture (`capture_ai_content=True`) is configured in development environments.

---

## Audit Event Immutability

Audit events are append-only. Ordinary application code cannot rewrite or mutate historical audit events. Any attempt to overwrite or delete audit entries raises `AuditImmutabilityError`.

---

## OpenTelemetry Exporters

Module 33 supports OpenTelemetry-compatible telemetry formats:
- `InMemoryExporter` (default for local development & testing)
- `ConsoleExporter` (structured stdout/stderr formatting)
- `OTLPExporter` (optional gRPC/HTTP OTLP collector backend)

If an external OTLP collector is unreachable, MAX degrades gracefully without crashing execution.

---

## API Reference (`/api/v1/observability`)

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Health status of observability storage and exporters |
| `/logs` | `GET` | Query structured, secret-redacted log entries |
| `/metrics` | `GET` | Retrieve metric aggregations and counters |
| `/traces` | `GET` | Search distributed execution traces |
| `/traces/{trace_id}` | `GET` | Retrieve trace detail with child execution spans |
| `/executions/{execution_id}` | `GET` | Derived step-by-step execution timeline |
| `/audit` | `GET` | Search append-only security & system audit records |
| `/audit/{event_id}` | `GET` | Single audit record detail |
| `/components` | `GET` | Registered observable components |
| `/errors` | `GET` | Recorded error records |
| `/statistics` | `GET` | System operational statistics summary |

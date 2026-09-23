# Module 14 — Tool Registry

## 1. Purpose
The Tool Registry is responsible for representing, discovering, versioning, resolving, schema-validating, and orchestrating tool invocation requests in the Max Personal AI system.

It acts as an abstraction and coordination boundary between AI Agents (Module 13) and future Permission (Module 15) and Execution (Modules 16+) layers.

> **CRITICAL SECURITY BOUNDARY**:
> The Tool Registry is **NOT** a computer control or system execution engine. High-risk and future tool definitions (e.g. `terminal.execute`, `filesystem.write`) terminate at the permission/execution boundary (`NOT_IMPLEMENTED`).

## 2. Architectural Role
```
User -> Conversation -> Context -> Reasoning -> Plan -> Tasks -> Agents -> Tool Registry -> Permission Engine -> Execution Layer
```
- Module 13: "Which agent coordinates the work?"
- Module 14: "What tools exist, and how should invocation requests be structured and validated?"
- Module 15: "Is this tool invocation permitted?"
- Module 16+: "Perform real-world system actions."

## 3. Domain Model
- `Tool`: Core entity representing a tool definition with ID, name, version, category, capabilities, risk level, input schema, output schema, status, and configuration.
- `ToolInputSchema` & `ToolOutputSchema`: Structured schemas detailing property field types, required fields, constraints, and allowed values.
- `ToolDescriptor`: Compact AI-friendly representation prepared for context insertion.
- `ToolInvocation`: Representation of a tool usage request lifecycle (`CREATED`, `VALIDATING`, `WAITING_PERMISSION`, `READY`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`).
- `ToolInvocationResult`: Structured output payload and duration.
- `ToolInvocationFailure`: Diagnostic failure taxonomy.
- `ToolEvent` & `ToolTrace`: Immutable audit trail tracking operational events.

## 4. Development Tools
- `echo.test`: Pure in-memory echo tool.
- `math.calculate`: Pure in-memory arithmetic calculator (`add`, `subtract`, `multiply`, `divide`).
- `text.transform`: Pure in-memory string transformer (`uppercase`, `lowercase`, `trim`).

## 5. REST API Reference
All endpoints are mounted under `/api/v1/tools`:
- `POST /api/v1/tools`: Register a tool.
- `GET /api/v1/tools`: List tools with filtering and pagination.
- `GET /api/v1/tools/search`: Search tool descriptors.
- `GET /api/v1/tools/capabilities`: Discover tools by capability.
- `POST /api/v1/tools/resolve`: Resolve tool reference.
- `GET /api/v1/tools/{tool_id}`: Retrieve tool by ID.
- `PATCH /api/v1/tools/{tool_id}`: Update tool properties.
- `DELETE /api/v1/tools/{tool_id}`: Archive/delete tool.
- `POST /api/v1/tools/{tool_id}/activate`: Transition status to ACTIVE.
- `POST /api/v1/tools/{tool_id}/disable`: Transition status to DISABLED.
- `POST /api/v1/tools/invocations`: Execute tool invocation pipeline.
- `GET /api/v1/tools/invocations/{invocation_id}`: Retrieve invocation record.
- `POST /api/v1/tools/invocations/{invocation_id}/cancel`: Cancel invocation.
- `GET /api/v1/tools/invocations/{invocation_id}/trace`: Retrieve audit trace.

## 6. Testing & Verification
- Unit tests: Schema validation, lifecycle state machine, resolver, dev tools execution.
- Integration tests: Module 13 Agent `ToolRequestIntent` integration, REST API routes.
- E2E tests: Full acceptance flow (register -> activate -> discover -> resolve -> invoke -> validate output -> trace).

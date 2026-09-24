# Module 20 — Browser Agent

## Overview

Module 20 implements the **Browser Agent** for the Max Personal AI runtime. It provides controlled, permission-aware, observable, and auditable browser automation capabilities.

It establishes a strict separation of responsibilities:
- **Module 20 (Browser Agent)**: "How Max interacts with a browser" (session management, DOM clicks, typing, navigation, tab switching, screenshot capture, safe downloads/uploads).
- **Module 21 (Web Intelligence)**: "How Max understands/researches the web" (future module).

---

## Architecture

```
User / Agent
     ↓
Browser Intent
     ↓
Browser Agent (BrowserService)
     ↓
Permission Engine (Module 15 PermissionGate)
     ↓
Browser Policy (BrowserPolicyService)
     ↓
Browser Session & Tabs
     ↓
Playwright / Mock Backend
     ↓
Browser Engine (Chromium/Firefox)
     ↓
Observe Page & Verify State
     ↓
Result & Audit Event (BrowserAuditRepository)
```

The permission boundary **always** remains between intent and execution. Unrestricted browser operations are strictly rejected.

---

## Key Capabilities

1. **Session & Tab Management**: Isolated browser contexts per owner ID with full lifecycle tracking (CREATE, INITIALIZING, READY, NAVIGATING, OBSERVING, EXECUTING, WAITING, ERROR, CLOSING, CLOSED).
2. **Navigation & URL Security**: Validation of schemes (`http://`, `https://` allowed; dangerous schemes `javascript:`, `file:`, `data:`, `chrome:` blocked) and domain policy check (allow/blocklists, subdomains, temporary grants).
3. **Structured Page Observation**: Extract bounded page elements (links, headings, buttons, inputs, forms) while enforcing maximum length limits to prevent context exhaustion.
4. **DOM Interactions**: Stable selector-based click, type, select, scroll, and wait conditions. Sensitive field classification masks secrets from logs and observations.
5. **Prompt Injection Defense**: Web page content is untrusted data. Extracted text is tagged as `UNTRUSTED_WEB_CONTENT` and sanitized so prompt injection payloads cannot alter system prompts or security policies.
6. **Download & Upload Management**: Integrates with Module 17 Filesystem Agent for path validation and sandboxing to prevent path traversal or unauthorized file access.
7. **Action Verification**: Browser actions return verification states (`VERIFIED`, `ACTION_COMPLETED_UNVERIFIED`, `FAILED`) based on post-execution DOM observation.
8. **Tool Integration**: Registers 22 browser tools with Module 14 `ToolRegistry`.

---

## API Endpoints

- `GET /api/v1/browser/health` - Subsystem health & Playwright availability.
- `POST /api/v1/browser/sessions` - Create isolated browser session.
- `GET /api/v1/browser/sessions` - List sessions.
- `DELETE /api/v1/browser/sessions/{session_id}` - Close session.
- `POST /api/v1/browser/sessions/{session_id}/tabs` - Create tab.
- `POST /api/v1/browser/sessions/{session_id}/tabs/{tab_id}/navigate` - Controlled navigation.
- `POST /api/v1/browser/sessions/{session_id}/tabs/{tab_id}/observe` - Extract page observation.
- `POST /api/v1/browser/sessions/{session_id}/tabs/{tab_id}/click` - Click DOM element.
- `POST /api/v1/browser/sessions/{session_id}/tabs/{tab_id}/type` - Type text into input field.
- `POST /api/v1/browser/sessions/{session_id}/tabs/{tab_id}/screenshot` - Capture screenshot.
- `POST /api/v1/browser/sessions/{session_id}/tabs/{tab_id}/download` - Download file securely.
- `POST /api/v1/browser/sessions/{session_id}/tabs/{tab_id}/upload` - Upload file securely.

---

## Safety & Security Model

- **The Web is Untrusted**: Web content provides information, never authority.
- **Module 15 Permission Gate**: Every sensitive action evaluates policy (`ALLOW`, `DENY`, `REQUIRE_APPROVAL`).
- **Module 17 Filesystem Protection**: Downloads and uploads enforce sandbox boundaries.
- **Sensitive Input Redaction**: Passwords, secrets, and sensitive field entries are redacted from logs and audit events.

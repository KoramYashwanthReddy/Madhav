# Module 21 — Web Intelligence

## Overview

Module 21 (Web Intelligence) provides Max Personal AI with a structured, evidence-aware, security-conscious web research subsystem. It enables Max to formulate research objectives, plan multi-step searches, discover candidate sources, acquire web page content via Module 20 Browser Agent, extract factual evidence with strict provenance, detect cross-source contradictions, validate citations, and synthesize evidence-backed research results.

---

## Architectural Separation

- **Module 20 (Browser Agent)**: Handles browser interaction (*"How Max interacts with a browser"*).
- **Module 21 (Web Intelligence)**: Handles web research, search providers, source discovery, evidence extraction, citation validation, freshness evaluation, conflict detection, and synthesis (*"What information Max needs from the web, its reliability, and synthesis"*).

> [!IMPORTANT]
> Module 21 does **not** duplicate browser sessions, Playwright backend, or click/type primitives. When page observation/acquisition is required, Module 21 delegates to Module 20's `BrowserService`.

---

## 10-Stage Research Lifecycle

```
CREATED → PLANNING → QUERYING → SEARCHING → COLLECTING → EXTRACTING → VALIDATING → COMPARING → SYNTHESIZING → COMPLETED
```

1. **CREATED**: Research request initialized with topic, question, scope, mode, and budget constraints.
2. **PLANNING**: `ResearchPlanner` constructs step-by-step `ResearchPlan`.
3. **QUERYING**: `QueryPlanner` generates complementary primary, technical, official, recent, and alternative search queries.
4. **SEARCHING**: `SourceDiscoveryService` queries `BaseSearchProvider` (e.g. `MockSearchProvider`), classifies source types, and evaluates authority/freshness.
5. **COLLECTING**: `ContentAcquisitionService` fetches page content using Module 20 `BrowserService`.
6. **EXTRACTING**: `ContentExtractionService` & `EvidenceService` section document text and extract provenance-linked evidence claims.
7. **VALIDATING**: `CitationService` formats first-class citations (APA, MLA, Chicago, IEEE, Simple) and validates them against retrieved sources.
8. **COMPARING**: `EvidenceComparator` compares evidence across distinct sources to detect date mismatches, claim contradictions, and numerical discrepancies.
9. **SYNTHESIZING**: `ResearchSynthesisService` & `ResearchQualityChecker` compile summary findings, limitations, uncertainties, and quality scores.
10. **COMPLETED**: `ResearchResult` persisted and made available via API and integrations.

---

## Security & Prompt Injection Defense

All web page content acquired from external websites is treated strictly as **`UNTRUSTED_WEB_CONTENT`** (DATA only).

- **No Instruction Execution**: Web content can never modify system prompts, identity, permissions, security policies, configuration, or execute arbitrary tools.
- **Signal Inspection**: `PromptInjectionEnforcer` scans text for injection attempts (`ignore previous instructions`, `reveal secrets`, `disable security`) and isolates the payload into sanitized data structures.
- **Domain Whitelisting & Blacklisting**: Enforces allowed/blocked domain policies before content acquisition.
- **Redacted Audit Trails**: `ResearchAuditService` redacts passwords, tokens, API keys, and secret credentials from audit logs.

---

## Integrations

- **Module 02 (Configuration)**: Powered by `WebIntelligenceSettings`.
- **Module 10 (RAG & Retrieval)**: `WebRAGIntegrationAdapter` prepares research evidence chunks for vector indexing.
- **Module 11 (Reasoning & Planning)**: `WebReasoningIntegrationAdapter` formats evidence premises and conflicts for logical reasoning.
- **Module 14 (Tool Registry)**: Pre-registers 8 built-in tools (`web.search`, `web.research`, `web.source.inspect`, `web.extract`, `web.compare`, `web.citations`, `web.fact_check`, `web.research.status`).
- **Module 20 (Browser Agent)**: Used exclusively for web page content acquisition and Javascript rendering.

---

## API Reference (`/api/v1/web-intelligence`)

- `POST /research` — Submit and execute research request
- `GET /research` — List research requests
- `GET /research/{research_id}` — Retrieve full research result
- `POST /research/{research_id}/cancel` — Cancel active research
- `GET /research/{research_id}/status` — Check operational status
- `GET /research/{research_id}/sources` — List candidate sources
- `GET /research/{research_id}/findings` — Retrieve key findings
- `GET /research/{research_id}/evidence` — Retrieve extracted evidence
- `GET /research/{research_id}/citations` — Retrieve formatted citations
- `GET /research/{research_id}/conflicts` — Retrieve detected conflicts
- `POST /search` — Execute direct search query
- `GET /sources/{source_id}` — Retrieve source details
- `GET /health` — Subsystem health endpoint

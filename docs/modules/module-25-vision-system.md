# Module 25 — Vision System Architecture & Design Documentation

## Executive Summary
Module 25 introduces the **Vision System** to Max Personal AI. It provides a comprehensive, provider-neutral visual perception and analysis framework capable of processing static images, UI screenshots, diagram schematics, chart figures, and document pages. The module enforces strict security controls (treating all optical text and image inputs as `UNTRUSTED_DATA`), defends against visual prompt injection, prevents credential leaks, and integrates seamlessly with Module 14 (`ToolRegistryService`), Module 15 (`PermissionGate`), Module 16 (`ComputerControlService`), and Module 24 (`DocumentIntelligence`).

---

## Architectural Principles & Layout

### Single Entry Point Pattern
All calls to the Vision System must pass through `VisionService` (`src/max/vision/services/vision_service.py`). No caller (agent, tool, API route, or background job) directly accesses provider SDKs or internal preprocessors.

```
Caller (Agent / Tool / API / UI)
          │
          ▼
    VisionService (Facade)
          │
          ├──> ImageValidator & ImagePreprocessor (Decompression bomb & size checks)
          ├──> VisionSecurityEnforcer (Permission gate, injection & credential checks)
          ├──> VisionCache (SHA-256 content-hash keyed LRU result cache)
          └──> VisionProvider (Provider-neutral abstraction: Mock, OpenAI, Anthropic, Ollama)
```

---

## Directory Structure

```
src/max/vision/
├── __init__.py                     # Module entry point & docstring
├── container.py                    # DI container (VisionContainer)
├── api/
│   ├── __init__.py
│   └── routes.py                   # FastAPI router (/api/v1/vision/*)
├── domain/
│   ├── __init__.py
│   ├── enums.py                    # Formats, capabilities, confidence levels, etc.
│   ├── exceptions.py               # Domain exceptions hierarchy
│   └── models.py                   # Dataclasses & Pydantic models for visual perception
├── preprocessing/
│   ├── __init__.py
│   ├── preprocessor.py             # PIL-based deterministic preprocessing & normalization
│   └── validator.py                # Magic-byte format detection & dimension limits
├── providers/
│   ├── __init__.py
│   ├── base.py                     # VisionProvider abstract base class
│   └── mock_provider.py            # High-fidelity mock provider implementation
├── security/
│   ├── __init__.py
│   └── enforcer.py                 # Security controls, injection & credential detection
└── services/
    ├── __init__.py
    ├── tool_integration.py         # M14 ToolRegistry registration (14 vision tools)
    └── vision_service.py           # Facade orchestrator & caching layer
```

---

## Core Capabilities & Features

1. **OCR (Optical Character Recognition)**:
   - Extracts structured text blocks, line coordinates, line angles, bounding boxes, reading order, and confidence scores.
   - Enforces prompt injection shielding: extracted text is wrapped as `UNTRUSTED_DATA`.

2. **Object Detection**:
   - Detects visual objects, returns 2D bounding boxes (`[ymin, xmin, ymax, xmax]`), area ratios, label tags, and confidence scores.

3. **UI Element Analysis**:
   - Parses UI screenshots into actionable UI elements (buttons, input fields, text labels, icons, checkboxes, sliders).
   - Provides element coordinates for Module 16 computer control actions.

4. **Image Description & Captioning**:
   - Generates natural-language visual summaries, detailed descriptions, and key visual entity listings.

5. **Classification**:
   - Assigns multi-label categorization and taxonomy classes to visual media.

6. **Chart & Diagram Analysis**:
   - Chart analysis extracts titles, chart types, data series, axis labels, and data points.
   - Diagram analysis extracts nodes, edges, topology relationships, and text annotations.

7. **Document Page Visual Analysis**:
   - Combines layout analysis, visual element detection, header/footer separation, and page-level OCR.

---

## Security & Defense Layer

- **Decompression Bomb Defense**: Dimension limits (max width 8192px, max height 8192px, max total 33MP) enforced before full decoding.
- **Magic-Byte Signature Verification**: Rejects format spoofing; validates PNG, JPEG, WEBP, BMP, TIFF, and GIF signatures.
- **Prompt Injection Defense**: Scans extracted text for system instructions, override attempts, or malicious prompts.
- **Credential Protection**: Detects API keys, passwords, and tokens visible in images or screenshots.
- **Camera & Screen Capture Gates**: Verifies Module 15 security settings before capturing live camera streams or host screenshots.

---

## Verification & Unit Testing

- Comprehensive test suite: `tests/unit/test_vision_system.py`
- Total Test Coverage: **119 / 119 PASSED** ✅

```bash
python -m pytest tests/unit/test_vision_system.py -v --tb=short
```

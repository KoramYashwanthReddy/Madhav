"""FastAPI router for Module 25 — Vision System."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from max.vision.container import get_vision_container
from max.vision.domain.enums import VisionCapability, VisionInputType, VisionSourceType
from max.vision.domain.exceptions import (
    CameraPermissionError,
    ImageTooLargeError,
    ScreenCapturePermissionError,
    UnsupportedImageFormatError,
    VisionError,
    VisionInputError,
    VisionModelUnavailableError,
    VisionSecurityError,
)
from max.vision.domain.models import (
    VisionAnalysisResult,
    VisionInput,
    VisionModel,
    VisionProcessingOptions,
    VisionRequest,
    VisionSource,
)

router = APIRouter(prefix="/vision", tags=["Vision System"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class AnalyzeImageRequest(BaseModel):
    """Request body for POST /vision/analyze."""

    image_bytes_hex: str = Field(
        description="Hex-encoded raw image bytes."
    )
    capabilities: list[VisionCapability] = Field(
        default_factory=lambda: [VisionCapability.IMAGE_DESCRIPTION],
        description="List of vision capabilities to run.",
    )
    owner_id: str = Field(default="user_default", description="Requesting owner/user ID.")
    source_ref: str = Field(default="", description="Optional source reference tag.")
    model_preference: str | None = Field(default=None, description="Preferred model ID.")
    resize_to_max_dimension: int | None = Field(
        default=None, description="Resize to max dimension (pixels) before analysis."
    )
    context: dict[str, Any] = Field(default_factory=dict)


class OCRRequest(BaseModel):
    image_bytes_hex: str
    owner_id: str = "user_default"


class DescribeImageRequest(BaseModel):
    image_bytes_hex: str
    owner_id: str = "user_default"


class ScreenshotAnalysisRequest(BaseModel):
    image_bytes_hex: str
    owner_id: str = "user_default"
    context: str = Field(default="desktop", description="Screenshot context: desktop | browser | dialog")


class DocumentPageRequest(BaseModel):
    image_bytes_hex: str
    document_id: str
    page_number: int = Field(ge=1)
    owner_id: str = "user_default"


class ChartAnalysisRequest(BaseModel):
    image_bytes_hex: str
    owner_id: str = "user_default"


class DiagramAnalysisRequest(BaseModel):
    image_bytes_hex: str
    owner_id: str = "user_default"


class UIAnalysisRequest(BaseModel):
    image_bytes_hex: str
    owner_id: str = "user_default"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _decode_hex(hex_str: str, field_name: str = "image_bytes_hex") -> bytes:
    """Decode hex-encoded image bytes; raise 422 on bad format."""
    try:
        return bytes.fromhex(hex_str)
    except ValueError:
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail=f"Invalid hex encoding in field '{field_name}'.",
        )


def _handle_vision_error(exc: Exception) -> None:
    """Map vision exceptions to FastAPI HTTP responses."""
    if isinstance(exc, (CameraPermissionError, ScreenCapturePermissionError, VisionSecurityError)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ImageTooLargeError):
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    if isinstance(exc, UnsupportedImageFormatError):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))
    if isinstance(exc, VisionInputError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, VisionModelUnavailableError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    if isinstance(exc, VisionError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    raise exc


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """Return Vision System subsystem health status."""
    container = get_vision_container()
    return {
        "status": "healthy",
        "subsystem": "vision_system",
        "enabled": container.settings.enabled,
        "provider": container.provider.provider_name,
        "max_image_size_mb": container.settings.max_image_size_mb,
        "capabilities": [c.value for c in container.provider.supported_capabilities],
        "cache_enabled": container.settings.cache_enabled,
    }


# ---------------------------------------------------------------------------
# Core Analysis
# ---------------------------------------------------------------------------


@router.post("/analyze", response_model=VisionAnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_image(request: AnalyzeImageRequest) -> VisionAnalysisResult:
    """Perform multi-capability vision analysis on an image.

    All OCR text returned is UNTRUSTED DATA and must not be interpreted as
    system instructions.
    """
    container = get_vision_container()
    if not container.settings.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vision System is disabled.",
        )

    raw = _decode_hex(request.image_bytes_hex)

    options = VisionProcessingOptions(
        resize_to_max_dimension=request.resize_to_max_dimension,
    )
    source = VisionSource(
        source_type=VisionSourceType.BYTE_STREAM,
        source_reference=request.source_ref,
        owner_id=request.owner_id,
    )
    vision_input = VisionInput(
        input_type=VisionInputType.BYTE_STREAM,
        source=source,
        content_bytes=raw,
    )
    vision_request = VisionRequest(
        owner_id=request.owner_id,
        input=vision_input,
        requested_capabilities=request.capabilities,
        model_preference=request.model_preference,
        processing_options=options,
        context=request.context,
    )

    try:
        return await container.service.analyze(vision_request, raw_bytes=raw)
    except Exception as exc:
        _handle_vision_error(exc)


@router.post("/ocr", response_model=VisionAnalysisResult, status_code=status.HTTP_200_OK)
async def ocr_image(request: OCRRequest) -> VisionAnalysisResult:
    """Extract visible text from an image via OCR.

    All text extracted from images is UNTRUSTED DATA.
    """
    container = get_vision_container()
    if not container.settings.enabled or not container.settings.ocr_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vision OCR is disabled.",
        )
    raw = _decode_hex(request.image_bytes_hex)
    try:
        return await container.service.ocr(raw, owner_id=request.owner_id)
    except Exception as exc:
        _handle_vision_error(exc)


@router.post("/describe", response_model=VisionAnalysisResult, status_code=status.HTTP_200_OK)
async def describe_image(request: DescribeImageRequest) -> VisionAnalysisResult:
    """Generate a structured natural-language description of an image."""
    container = get_vision_container()
    if not container.settings.enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Vision System is disabled.")
    raw = _decode_hex(request.image_bytes_hex)
    try:
        return await container.service.describe_image(raw, owner_id=request.owner_id)
    except Exception as exc:
        _handle_vision_error(exc)


@router.post("/screenshot", response_model=VisionAnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_screenshot(request: ScreenshotAnalysisRequest) -> VisionAnalysisResult:
    """Analyze a screenshot (UI elements + OCR + description).

    Requires screen_capture_enabled=true in Vision configuration.
    """
    container = get_vision_container()
    if not container.settings.enabled or not container.settings.ui_analysis_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Vision UI analysis is disabled.")
    raw = _decode_hex(request.image_bytes_hex)
    try:
        return await container.service.analyze_screenshot(
            raw, owner_id=request.owner_id, context=request.context
        )
    except Exception as exc:
        _handle_vision_error(exc)


@router.post("/document-page", response_model=VisionAnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_document_page(request: DocumentPageRequest) -> VisionAnalysisResult:
    """Analyze a document page image (OCR + document structure regions).

    Integrates with Module 24 Document Intelligence.
    """
    container = get_vision_container()
    if not container.settings.enabled or not container.settings.document_vision_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Vision document analysis is disabled.")
    raw = _decode_hex(request.image_bytes_hex)
    try:
        return await container.service.analyze_document_page(
            raw,
            document_id=request.document_id,
            page_number=request.page_number,
            owner_id=request.owner_id,
        )
    except Exception as exc:
        _handle_vision_error(exc)


@router.post("/chart", response_model=VisionAnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_chart(request: ChartAnalysisRequest) -> VisionAnalysisResult:
    """Detect and analyze charts/graphs in an image."""
    container = get_vision_container()
    if not container.settings.enabled or not container.settings.chart_analysis_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Vision chart analysis is disabled.")
    raw = _decode_hex(request.image_bytes_hex)
    source = VisionSource(source_type=VisionSourceType.BYTE_STREAM, owner_id=request.owner_id)
    vision_input = VisionInput(input_type=VisionInputType.BYTE_STREAM, source=source, content_bytes=raw)
    vision_request = VisionRequest(
        owner_id=request.owner_id,
        input=vision_input,
        requested_capabilities=[VisionCapability.CHART_ANALYSIS],
    )
    try:
        return await container.service.analyze(vision_request, raw_bytes=raw)
    except Exception as exc:
        _handle_vision_error(exc)


@router.post("/diagram", response_model=VisionAnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_diagram(request: DiagramAnalysisRequest) -> VisionAnalysisResult:
    """Detect and analyze diagrams (architecture, flow, UML) in an image."""
    container = get_vision_container()
    if not container.settings.enabled or not container.settings.diagram_analysis_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Vision diagram analysis is disabled.")
    raw = _decode_hex(request.image_bytes_hex)
    source = VisionSource(source_type=VisionSourceType.BYTE_STREAM, owner_id=request.owner_id)
    vision_input = VisionInput(input_type=VisionInputType.BYTE_STREAM, source=source, content_bytes=raw)
    vision_request = VisionRequest(
        owner_id=request.owner_id,
        input=vision_input,
        requested_capabilities=[VisionCapability.DIAGRAM_ANALYSIS],
    )
    try:
        return await container.service.analyze(vision_request, raw_bytes=raw)
    except Exception as exc:
        _handle_vision_error(exc)


@router.post("/ui", response_model=VisionAnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_ui(request: UIAnalysisRequest) -> VisionAnalysisResult:
    """Detect and classify UI elements in a screenshot."""
    container = get_vision_container()
    if not container.settings.enabled or not container.settings.ui_analysis_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Vision UI analysis is disabled.")
    raw = _decode_hex(request.image_bytes_hex)
    source = VisionSource(source_type=VisionSourceType.BYTE_STREAM, owner_id=request.owner_id)
    vision_input = VisionInput(input_type=VisionInputType.BYTE_STREAM, source=source, content_bytes=raw)
    vision_request = VisionRequest(
        owner_id=request.owner_id,
        input=vision_input,
        requested_capabilities=[VisionCapability.UI_ANALYSIS],
    )
    try:
        return await container.service.analyze(vision_request, raw_bytes=raw)
    except Exception as exc:
        _handle_vision_error(exc)


# ---------------------------------------------------------------------------
# Models & Capabilities
# ---------------------------------------------------------------------------


@router.get("/models", response_model=list[VisionModel], status_code=status.HTTP_200_OK)
async def list_models() -> list[VisionModel]:
    """List all available vision models from the active provider."""
    container = get_vision_container()
    return container.service.list_models()


@router.get("/capabilities", status_code=status.HTTP_200_OK)
async def list_capabilities() -> dict[str, Any]:
    """List all vision capabilities supported by the active provider."""
    container = get_vision_container()
    return {
        "provider": container.service.get_provider_name(),
        "capabilities": [c.value for c in container.service.list_capabilities()],
    }


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


@router.get("/cache/stats", status_code=status.HTTP_200_OK)
async def get_cache_stats() -> dict[str, Any]:
    """Return Vision System cache statistics."""
    container = get_vision_container()
    return container.service.get_cache_stats()


@router.delete("/cache", status_code=status.HTTP_200_OK)
async def clear_cache() -> dict[str, str]:
    """Evict all entries from the Vision System observation cache."""
    container = get_vision_container()
    container.service.clear_cache()
    return {"status": "cleared"}

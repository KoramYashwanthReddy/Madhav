"""VisionService — master facade for Module 25 — Vision System.

VisionService is the ONLY entry point for all vision analysis.
All callers (agents, tools, API routes, adapters) use this class.

Architecture:
    Caller
    ↓
    VisionService.analyze(request)
    ↓
    ImageValidator.validate()        # size, format, dimensions (security gate)
    ↓
    ImagePreprocessor.preprocess()   # normalize orientation, resize if needed
    ↓
    VisionSecurityEnforcer           # pre-flight permission + policy check
    ↓
    VisionProvider.analyze()         # provider-neutral analysis
    ↓
    VisionSecurityEnforcer           # post-flight: wrap OCR as untrusted, safety metadata
    ↓
    Cache (deterministic, keyed by content hash + capabilities)
    ↓
    VisionAnalysisResult             # canonical normalized result

Vision OBSERVES. It does NOT decide. It does NOT execute.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

from max.vision.domain.enums import (
    VisionCapability,
    VisionFormat,
    VisionInputType,
    VisionProcessingStatus,
)
from max.vision.domain.exceptions import (
    ImageTooLargeError,
    UnsupportedImageFormatError,
    VisionError,
    VisionInputError,
    VisionModelUnavailableError,
    VisionProcessingTimeoutError,
)
from max.vision.domain.models import (
    VisionAnalysisResult,
    VisionDimensions,
    VisionImage,
    VisionInput,
    VisionMetadata,
    VisionModel,
    VisionModelConfiguration,
    VisionProcessingError,
    VisionRequest,
    VisionSource,
)
from max.vision.preprocessing.preprocessor import ImagePreprocessor
from max.vision.preprocessing.validator import ImageValidator
from max.vision.providers.base import VisionProvider
from max.vision.security.enforcer import VisionSecurityEnforcer

logger = logging.getLogger(__name__)


class VisionCache:
    """Simple in-memory deterministic cache for vision results.

    Key: SHA-256(content_hash + sorted capability list)
    Entries expire after cache_ttl_seconds.
    """

    def __init__(self, max_entries: int = 1000, ttl_seconds: int = 3600) -> None:
        self._store: dict[str, tuple[VisionAnalysisResult, float]] = {}
        self._max_entries = max_entries
        self._ttl = ttl_seconds

    def _make_key(self, content_hash: str, capabilities: list[VisionCapability]) -> str:
        cap_str = ",".join(sorted(c.value for c in capabilities))
        return hashlib.sha256(f"{content_hash}:{cap_str}".encode()).hexdigest()

    def get(
        self, content_hash: str, capabilities: list[VisionCapability]
    ) -> VisionAnalysisResult | None:
        key = self._make_key(content_hash, capabilities)
        entry = self._store.get(key)
        if entry is None:
            return None
        result, stored_at = entry
        if time.monotonic() - stored_at > self._ttl:
            del self._store[key]
            return None
        return result

    def put(
        self,
        content_hash: str,
        capabilities: list[VisionCapability],
        result: VisionAnalysisResult,
    ) -> None:
        if len(self._store) >= self._max_entries:
            # Evict oldest entry
            oldest_key = next(iter(self._store))
            del self._store[oldest_key]
        key = self._make_key(content_hash, capabilities)
        self._store[key] = (result, time.monotonic())

    def clear(self) -> None:
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)


class VisionService:
    """Master Vision System facade.

    This is the only public interface for all vision operations.
    Handles validation, preprocessing, security, routing, and caching.
    """

    def __init__(
        self,
        provider: VisionProvider,
        validator: ImageValidator,
        preprocessor: ImagePreprocessor,
        security_enforcer: VisionSecurityEnforcer,
        cache: VisionCache | None = None,
        cache_enabled: bool = True,
        default_model_id: str = "mock-vision-v1",
        default_capabilities: list[VisionCapability] | None = None,
    ) -> None:
        self._provider = provider
        self._validator = validator
        self._preprocessor = preprocessor
        self._security = security_enforcer
        self._cache = cache or VisionCache()
        self._cache_enabled = cache_enabled
        self._default_model_id = default_model_id
        self._default_capabilities = default_capabilities or [VisionCapability.IMAGE_DESCRIPTION]

    # -----------------------------------------------------------------------
    # Core Analysis API
    # -----------------------------------------------------------------------

    async def analyze(
        self,
        request: VisionRequest,
        raw_bytes: bytes | None = None,
    ) -> VisionAnalysisResult:
        """Execute a full vision analysis pipeline.

        Args:
            request:   Fully-formed VisionRequest.
            raw_bytes: Raw image bytes (if not provided, must be in request.input.content_bytes).

        Returns:
            Normalized VisionAnalysisResult.

        Raises:
            VisionInputError: on bad input.
            ImageTooLargeError: on size/dimension violation.
            UnsupportedImageFormatError: on unsupported format.
            VisionModelUnavailableError: if no provider can handle the request.
        """
        start = time.monotonic()
        data = raw_bytes or request.input.content_bytes

        if not data:
            return self._error_result(
                request.request_id,
                VisionProcessingStatus.FAILED,
                "MISSING_DATA",
                "No image data provided in request.",
            )

        # --- Pre-flight security checks ---
        try:
            self._pre_flight_security(request, data)
        except VisionError as exc:
            return self._error_result(
                request.request_id,
                VisionProcessingStatus.FAILED,
                type(exc).__name__,
                str(exc),
            )

        # --- Validate image ---
        try:
            metadata = self._validator.validate(data)
        except (ImageTooLargeError, UnsupportedImageFormatError, VisionInputError) as exc:
            return self._error_result(
                request.request_id,
                VisionProcessingStatus.FAILED,
                type(exc).__name__,
                str(exc),
            )

        # --- Cache lookup ---
        if self._cache_enabled and metadata.content_hash:
            cached = self._cache.get(metadata.content_hash, request.requested_capabilities)
            if cached is not None:
                logger.debug(
                    "Vision cache HIT for content_hash=%s", metadata.content_hash[:12]
                )
                return cached

        # --- Preprocess ---
        try:
            preprocessed = self._preprocessor.preprocess(
                data, metadata.format, request.processing_options
            )
            if preprocessed.width > 0 and preprocessed.height > 0:
                metadata = metadata.model_copy(
                    update={
                        "dimensions": VisionDimensions(
                            width=preprocessed.width,
                            height=preprocessed.height,
                        )
                    }
                )
            analysis_data = preprocessed.data
        except Exception as exc:
            logger.warning("Preprocessing failed, falling back to raw bytes: %s", exc)
            analysis_data = data

        # --- Build VisionImage ---
        image = VisionImage(
            content_hash=metadata.content_hash,
            source=request.input.source,
            metadata=metadata,
        )

        # --- Build model config ---
        model_config = VisionModelConfiguration(
            model_id=request.model_preference or self._default_model_id,
        )

        # --- Ensure at least one capability ---
        caps = request.requested_capabilities or self._default_capabilities

        effective_request = request.model_copy(update={"requested_capabilities": caps})

        # --- Invoke provider ---
        try:
            result = await self._provider.analyze(
                image=image,
                data=analysis_data,
                request=effective_request,
                model_config=model_config,
            )
        except Exception as exc:
            logger.exception("Vision provider failed for request %s", request.request_id)
            return self._error_result(
                request.request_id,
                VisionProcessingStatus.FAILED,
                "PROVIDER_ERROR",
                f"Vision provider error: {exc}",
            )

        # --- Post-process security ---
        result = self._post_process_security(result)

        # --- Timing ---
        elapsed_ms = (time.monotonic() - start) * 1000
        result = result.model_copy(update={"processing_time_ms": elapsed_ms})

        # --- Cache store ---
        if (
            self._cache_enabled
            and metadata.content_hash
            and result.status == VisionProcessingStatus.COMPLETED
        ):
            self._cache.put(metadata.content_hash, caps, result)

        logger.info(
            "Vision analysis completed: request=%s status=%s caps=%s time_ms=%.1f",
            request.request_id,
            result.status,
            [c.value for c in caps],
            elapsed_ms,
        )
        return result

    # -----------------------------------------------------------------------
    # Convenience Methods
    # -----------------------------------------------------------------------

    async def ocr(
        self,
        data: bytes,
        owner_id: str = "user_default",
        source_ref: str = "",
    ) -> VisionAnalysisResult:
        """Shortcut: perform OCR on raw image bytes."""
        return await self.analyze(
            self._make_simple_request(
                data, [VisionCapability.OCR], owner_id, source_ref
            ),
            raw_bytes=data,
        )

    async def describe_image(
        self,
        data: bytes,
        owner_id: str = "user_default",
        source_ref: str = "",
    ) -> VisionAnalysisResult:
        """Shortcut: generate a structured description of an image."""
        return await self.analyze(
            self._make_simple_request(
                data, [VisionCapability.IMAGE_DESCRIPTION], owner_id, source_ref
            ),
            raw_bytes=data,
        )

    async def analyze_screenshot(
        self,
        data: bytes,
        owner_id: str = "user_default",
        context: str = "desktop",
    ) -> VisionAnalysisResult:
        """Shortcut: analyze a screenshot (UI analysis + OCR + description)."""
        self._security.enforce_screen_capture_allowed(owner_id)
        caps = [
            VisionCapability.UI_ANALYSIS,
            VisionCapability.OCR,
            VisionCapability.IMAGE_DESCRIPTION,
        ]
        req = self._make_simple_request(data, caps, owner_id, source_ref="screenshot")
        req = req.model_copy(update={"context": {"screenshot_context": context}})
        return await self.analyze(req, raw_bytes=data)

    async def analyze_document_page(
        self,
        data: bytes,
        document_id: str,
        page_number: int,
        owner_id: str = "user_default",
    ) -> VisionAnalysisResult:
        """Shortcut: analyze a document page image (OCR + document structure)."""
        from max.vision.domain.enums import VisionInputType, VisionSourceType
        from max.vision.domain.models import VisionInput, VisionSource

        source = VisionSource(
            source_type=VisionSourceType.DOCUMENT_REFERENCE,
            source_reference=document_id,
            owner_id=owner_id,
            page_number=page_number,
            document_id=document_id,
        )
        vision_input = VisionInput(
            input_type=VisionInputType.DOCUMENT_PAGE,
            source=source,
            content_bytes=data,
        )
        req = VisionRequest(
            owner_id=owner_id,
            input=vision_input,
            requested_capabilities=[VisionCapability.DOCUMENT_ANALYSIS, VisionCapability.OCR],
        )
        return await self.analyze(req, raw_bytes=data)

    # -----------------------------------------------------------------------
    # Provider & Model Info
    # -----------------------------------------------------------------------

    def list_models(self) -> list[VisionModel]:
        """List all models available from the current provider."""
        return self._provider.supported_models()

    def list_capabilities(self) -> list[VisionCapability]:
        """List all capabilities supported by the current provider."""
        return self._provider.supported_capabilities

    def get_provider_name(self) -> str:
        """Return the name of the active provider."""
        return self._provider.provider_name

    def get_cache_stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        return {
            "enabled": self._cache_enabled,
            "entries": self._cache.size,
        }

    def clear_cache(self) -> None:
        """Evict all cache entries."""
        self._cache.clear()

    # -----------------------------------------------------------------------
    # Internal Helpers
    # -----------------------------------------------------------------------

    def _pre_flight_security(self, request: VisionRequest, data: bytes) -> None:
        """Run pre-analysis security checks."""
        inp = request.input
        if inp.input_type == VisionInputType.SCREENSHOT or inp.input_type == VisionInputType.BROWSER_SCREENSHOT:
            self._security.enforce_screen_capture_allowed(request.owner_id)
        if inp.input_type == VisionInputType.CAMERA_FRAME:
            self._security.enforce_camera_allowed(request.owner_id)
        if inp.file_path:
            self._security.enforce_file_image_allowed(inp.file_path, request.owner_id)

    def _post_process_security(self, result: VisionAnalysisResult) -> VisionAnalysisResult:
        """Apply post-analysis security: wrap OCR as untrusted, build safety metadata."""
        ocr_text = ""

        if result.ocr is not None:
            wrapped_ocr = self._security.wrap_ocr_as_untrusted(result.ocr)
            result = result.model_copy(update={"ocr": wrapped_ocr})
            ocr_text = result.ocr.full_text

        face_detected = result.safety.face_detected if result.safety else False
        safety = self._security.build_safety_metadata(
            ocr_text=ocr_text,
            face_detected=face_detected,
        )
        return result.model_copy(update={"safety": safety})

    def _make_simple_request(
        self,
        data: bytes,
        capabilities: list[VisionCapability],
        owner_id: str,
        source_ref: str,
    ) -> VisionRequest:
        """Build a minimal VisionRequest for convenience methods."""
        from max.vision.domain.enums import VisionInputType, VisionSourceType

        source = VisionSource(
            source_type=VisionSourceType.BYTE_STREAM,
            source_reference=source_ref,
            owner_id=owner_id,
        )
        vision_input = VisionInput(
            input_type=VisionInputType.BYTE_STREAM,
            source=source,
            content_bytes=data,
        )
        return VisionRequest(
            owner_id=owner_id,
            input=vision_input,
            requested_capabilities=capabilities,
        )

    @staticmethod
    def _error_result(
        request_id: str,
        status: VisionProcessingStatus,
        error_type: str,
        message: str,
        recoverable: bool = False,
    ) -> VisionAnalysisResult:
        """Build a failed VisionAnalysisResult with a structured error."""
        from datetime import UTC, datetime

        return VisionAnalysisResult(
            request_id=request_id,
            status=status,
            errors=[
                VisionProcessingError(
                    error_type=error_type,
                    message=message,
                    recoverable=recoverable,
                )
            ],
            completed_at=datetime.now(UTC),
        )

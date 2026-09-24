"""Domain models for Module 25 — Vision System.

All models are provider-neutral Pydantic types.
No provider-specific structures must appear here.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.vision.domain.enums import (
    VisionCapability,
    VisionChartType,
    VisionColorSpace,
    VisionConfidenceLevel,
    VisionFormat,
    VisionInputType,
    VisionModelCapability,
    VisionModelStatus,
    VisionObjectClass,
    VisionObservationType,
    VisionProcessingStatus,
    VisionSourceType,
    VisionUIElementType,
)

# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


class VisionPoint(BaseModel):
    """A 2D point in image/screen coordinates."""

    x: float
    y: float


class VisionBoundingBox(BaseModel):
    """Axis-aligned rectangular bounding box (image coordinates)."""

    x: float = Field(description="Left edge x-coordinate")
    y: float = Field(description="Top edge y-coordinate")
    width: float = Field(description="Box width in pixels")
    height: float = Field(description="Box height in pixels")

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2.0

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2.0

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height


class VisionPolygon(BaseModel):
    """Arbitrary polygon for region delineation."""

    points: list[VisionPoint] = Field(default_factory=list)


class VisionRegion(BaseModel):
    """A labeled region within an image."""

    region_id: str = Field(default_factory=lambda: f"vr_{uuid.uuid4().hex[:10]}")
    label: str = ""
    bounding_box: VisionBoundingBox | None = None
    polygon: VisionPolygon | None = None
    confidence: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Coordinate System
# ---------------------------------------------------------------------------


class VisionCoordinateSystem(BaseModel):
    """Describes the coordinate reference frame for bounding boxes."""

    source_width: float = Field(description="Source image/screen width in pixels")
    source_height: float = Field(description="Source image/screen height in pixels")
    coordinate_type: str = Field(
        default="IMAGE",
        description="Coordinate type: IMAGE | SCREEN | BROWSER_VIEWPORT | NORMALIZED",
    )

    def to_normalized(self, box: VisionBoundingBox) -> VisionBoundingBox:
        """Convert to 0-1 normalized coordinates."""
        if self.source_width <= 0 or self.source_height <= 0:
            return box
        return VisionBoundingBox(
            x=box.x / self.source_width,
            y=box.y / self.source_height,
            width=box.width / self.source_width,
            height=box.height / self.source_height,
        )

    def from_normalized(self, box: VisionBoundingBox) -> VisionBoundingBox:
        """Convert from 0-1 normalized to pixel coordinates."""
        return VisionBoundingBox(
            x=box.x * self.source_width,
            y=box.y * self.source_height,
            width=box.width * self.source_width,
            height=box.height * self.source_height,
        )


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


class VisionConfidence(BaseModel):
    """Explicit confidence representation with qualitative classification."""

    score: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0–1.0")
    level: VisionConfidenceLevel = VisionConfidenceLevel.UNCERTAIN

    @classmethod
    def from_score(
        cls,
        score: float,
        high_threshold: float = 0.85,
        medium_threshold: float = 0.60,
        low_threshold: float = 0.40,
    ) -> VisionConfidence:
        if score >= high_threshold:
            level = VisionConfidenceLevel.HIGH
        elif score >= medium_threshold:
            level = VisionConfidenceLevel.MEDIUM
        elif score >= low_threshold:
            level = VisionConfidenceLevel.LOW
        else:
            level = VisionConfidenceLevel.UNCERTAIN
        return cls(score=score, level=level)


# ---------------------------------------------------------------------------
# Safety & Privacy
# ---------------------------------------------------------------------------


class VisionSafetyMetadata(BaseModel):
    """Safety and privacy classification flags for a vision request/result."""

    prompt_injection_risk: bool = False
    contains_sensitive_text: bool = False
    face_detected: bool = False
    credential_pattern_detected: bool = False
    redaction_applied: bool = False
    redaction_regions: list[VisionBoundingBox] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Image Metadata
# ---------------------------------------------------------------------------


class VisionDimensions(BaseModel):
    """Image size information."""

    width: int = Field(ge=1, description="Image width in pixels")
    height: int = Field(ge=1, description="Image height in pixels")

    @property
    def total_pixels(self) -> int:
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height if self.height > 0 else 0.0


class VisionMetadata(BaseModel):
    """Extracted image metadata from file headers and EXIF."""

    format: VisionFormat = VisionFormat.UNKNOWN
    dimensions: VisionDimensions | None = None
    color_space: VisionColorSpace = VisionColorSpace.UNKNOWN
    file_size_bytes: int = 0
    content_hash: str = ""  # SHA-256 of raw bytes
    dpi_x: float | None = None
    dpi_y: float | None = None
    num_frames: int = 1
    has_transparency: bool = False
    exif: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Visual Input
# ---------------------------------------------------------------------------


class VisionSource(BaseModel):
    """Tracks where a visual input originated from."""

    source_type: VisionSourceType = VisionSourceType.TEMPORARY_REFERENCE
    source_reference: str = ""  # path, URL, document_id, etc.
    owner_id: str = "system"
    page_number: int | None = None
    document_id: str | None = None
    screenshot_context: str | None = None


class VisionImage(BaseModel):
    """A processed image ready for vision analysis.

    Content bytes are NOT stored here. This model stores
    a reference to the content hash and location, not raw bytes.
    """

    image_id: str = Field(default_factory=lambda: f"img_{uuid.uuid4().hex[:10]}")
    content_hash: str = ""
    source: VisionSource = Field(default_factory=VisionSource)
    metadata: VisionMetadata = Field(default_factory=VisionMetadata)
    is_valid: bool = True
    validation_warnings: list[str] = Field(default_factory=list)
    preprocessed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class VisionInput(BaseModel):
    """Raw input for a vision request (before validation/decoding)."""

    input_type: VisionInputType = VisionInputType.FILE
    source: VisionSource = Field(default_factory=VisionSource)
    # For byte stream inputs — kept None if referencing a file
    content_bytes: bytes | None = Field(default=None, exclude=True)
    file_path: str | None = None  # Only used pre-validation; routed through M17
    metadata_hints: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Vision Model
# ---------------------------------------------------------------------------


class VisionModel(BaseModel):
    """Provider-neutral vision model descriptor."""

    model_id: str
    name: str
    version: str = "1.0.0"
    provider: str
    capabilities: list[VisionModelCapability] = Field(default_factory=list)
    status: VisionModelStatus = VisionModelStatus.NOT_INSTALLED
    max_image_size_mb: float = 25.0
    max_width: int = 4096
    max_height: int = 4096
    metadata: dict[str, Any] = Field(default_factory=dict)

    def supports(self, cap: VisionModelCapability) -> bool:
        return cap in self.capabilities


class VisionModelConfiguration(BaseModel):
    """Runtime configuration supplied to a provider for a specific request."""

    model_id: str
    temperature: float = 0.0
    max_tokens: int | None = None
    detail_level: str = "auto"  # auto | low | high
    additional: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Vision Request
# ---------------------------------------------------------------------------


class VisionRequestId(BaseModel):
    """Typed wrapper for a vision request identifier."""

    value: str = Field(default_factory=lambda: f"vreq_{uuid.uuid4().hex[:12]}")


class VisionProcessingOptions(BaseModel):
    """Optional preprocessing/analysis directives for a vision request."""

    resize_to_max_dimension: int | None = None
    force_grayscale: bool = False
    crop_region: VisionBoundingBox | None = None
    rotate_degrees: float | None = None
    normalize_orientation: bool = True
    coordinate_system: str = "IMAGE"  # IMAGE | SCREEN | BROWSER_VIEWPORT


class VisionRequest(BaseModel):
    """Top-level vision analysis request (provider-neutral)."""

    request_id: str = Field(default_factory=lambda: f"vreq_{uuid.uuid4().hex[:12]}")
    owner_id: str = "user_default"
    input: VisionInput = Field(default_factory=VisionInput)
    requested_capabilities: list[VisionCapability] = Field(default_factory=list)
    model_preference: str | None = None
    processing_options: VisionProcessingOptions = Field(default_factory=VisionProcessingOptions)
    context: dict[str, Any] = Field(default_factory=dict)
    timeout: float = 60.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Provenance & Citations
# ---------------------------------------------------------------------------


class VisionProvenance(BaseModel):
    """Full provenance chain for a visual observation."""

    vision_request_id: str
    source_id: str = ""
    image_hash: str = ""
    model_id: str = ""
    model_version: str = ""
    provider: str = ""
    processing_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    region: VisionBoundingBox | None = None
    page_number: int | None = None
    document_id: str | None = None


class VisionCitation(BaseModel):
    """Human-readable citation for a visual observation."""

    citation_id: str = Field(default_factory=lambda: f"vcit_{uuid.uuid4().hex[:8]}")
    provenance: VisionProvenance
    summary: str = ""

    @property
    def formatted_citation(self) -> str:
        parts = [f"[vision:{self.provenance.vision_request_id}]"]
        if self.provenance.document_id:
            parts.append(f"doc:{self.provenance.document_id}")
        if self.provenance.page_number is not None:
            parts.append(f"page:{self.provenance.page_number}")
        if self.summary:
            parts.append(self.summary)
        return " ".join(parts)


# ---------------------------------------------------------------------------
# OCR Results
# ---------------------------------------------------------------------------


class VisionOCRWord(BaseModel):
    """A single OCR word with location and confidence."""

    text: str
    bounding_box: VisionBoundingBox | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    language: str | None = None


class VisionOCRLine(BaseModel):
    """A line of OCR text."""

    text: str
    bounding_box: VisionBoundingBox | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    words: list[VisionOCRWord] = Field(default_factory=list)
    reading_order: int | None = None


class VisionOCRBlock(BaseModel):
    """A block (paragraph / region) of OCR text."""

    block_id: str = Field(default_factory=lambda: f"ocrb_{uuid.uuid4().hex[:8]}")
    text: str
    bounding_box: VisionBoundingBox | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    lines: list[VisionOCRLine] = Field(default_factory=list)
    language: str | None = None


class VisionTextRegion(BaseModel):
    """A located text region (before full OCR processing)."""

    region_id: str = Field(default_factory=lambda: f"txt_{uuid.uuid4().hex[:8]}")
    bounding_box: VisionBoundingBox | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    estimated_text_length: int | None = None


class VisionOCRResult(BaseModel):
    """Complete OCR result for an image."""

    full_text: str = ""
    blocks: list[VisionOCRBlock] = Field(default_factory=list)
    confidence: VisionConfidence = Field(default_factory=lambda: VisionConfidence(score=1.0))
    language: str | None = None
    is_untrusted_data: bool = True  # Always treat OCR text as untrusted


# ---------------------------------------------------------------------------
# Object Detection
# ---------------------------------------------------------------------------


class VisionObject(BaseModel):
    """A single detected visual object."""

    object_id: str = Field(default_factory=lambda: f"obj_{uuid.uuid4().hex[:8]}")
    object_class: VisionObjectClass = VisionObjectClass.UNKNOWN
    label: str = ""
    confidence: VisionConfidence = Field(default_factory=lambda: VisionConfidence(score=0.5))
    bounding_box: VisionBoundingBox | None = None
    polygon: VisionPolygon | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source_model: str = ""


class VisionObjectDetection(BaseModel):
    """Complete object detection result for an image."""

    objects: list[VisionObject] = Field(default_factory=list)
    total_detected: int = 0
    model_id: str = ""

    def model_post_init(self, __context: Any) -> None:
        if self.total_detected == 0:
            self.total_detected = len(self.objects)


# ---------------------------------------------------------------------------
# UI Analysis
# ---------------------------------------------------------------------------


class VisionUIElement(BaseModel):
    """A detected UI element in a screenshot."""

    element_id: str = Field(default_factory=lambda: f"ui_{uuid.uuid4().hex[:8]}")
    element_type: VisionUIElementType = VisionUIElementType.UNKNOWN
    visible_text: str = ""
    bounding_box: VisionBoundingBox | None = None
    confidence: VisionConfidence = Field(default_factory=lambda: VisionConfidence(score=0.5))
    interaction_role: str | None = None  # e.g. "submit", "cancel", "navigate"
    is_enabled: bool | None = None
    is_visible: bool = True
    attributes: dict[str, Any] = Field(default_factory=dict)


class VisionUIAnalysis(BaseModel):
    """Complete UI analysis result for a screenshot."""

    elements: list[VisionUIElement] = Field(default_factory=list)
    layout_description: str = ""
    coordinate_system: VisionCoordinateSystem | None = None
    screenshot_context: str = ""  # e.g. "browser", "desktop", "dialog"


# ---------------------------------------------------------------------------
# Chart Analysis
# ---------------------------------------------------------------------------


class VisionChart(BaseModel):
    """A detected chart/graph in an image."""

    chart_id: str = Field(default_factory=lambda: f"chart_{uuid.uuid4().hex[:8]}")
    chart_type: VisionChartType = VisionChartType.UNKNOWN
    title: str | None = None
    x_axis_label: str | None = None
    y_axis_label: str | None = None
    legend_labels: list[str] = Field(default_factory=list)
    visible_data_labels: list[str] = Field(default_factory=list)
    observed_trends: list[str] = Field(default_factory=list)
    bounding_box: VisionBoundingBox | None = None
    confidence: VisionConfidence = Field(default_factory=lambda: VisionConfidence(score=0.5))
    notes: list[str] = Field(default_factory=list)  # Uncertainty notes


# ---------------------------------------------------------------------------
# Diagram Analysis
# ---------------------------------------------------------------------------


class VisionDiagramNode(BaseModel):
    """A node in a detected diagram."""

    node_id: str = Field(default_factory=lambda: f"node_{uuid.uuid4().hex[:6]}")
    label: str = ""
    bounding_box: VisionBoundingBox | None = None
    node_type: str = "unknown"


class VisionDiagramEdge(BaseModel):
    """A connector/edge in a detected diagram."""

    edge_id: str = Field(default_factory=lambda: f"edge_{uuid.uuid4().hex[:6]}")
    source_node_id: str = ""
    target_node_id: str = ""
    label: str = ""
    direction: str = "unknown"  # "→", "←", "↔", "unknown"


class VisionDiagram(BaseModel):
    """A detected diagram (architecture, flow, etc.)."""

    diagram_id: str = Field(default_factory=lambda: f"diag_{uuid.uuid4().hex[:8]}")
    diagram_type: str = "unknown"
    nodes: list[VisionDiagramNode] = Field(default_factory=list)
    edges: list[VisionDiagramEdge] = Field(default_factory=list)
    bounding_box: VisionBoundingBox | None = None
    confidence: VisionConfidence = Field(default_factory=lambda: VisionConfidence(score=0.5))
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Document Region
# ---------------------------------------------------------------------------


class VisionDocumentRegion(BaseModel):
    """A labeled region on a document page image."""

    region_id: str = Field(default_factory=lambda: f"dreg_{uuid.uuid4().hex[:8]}")
    region_type: str = "unknown"  # "heading", "body", "table", "figure", "footer", etc.
    bounding_box: VisionBoundingBox | None = None
    ocr_result: VisionOCRResult | None = None
    confidence: VisionConfidence = Field(default_factory=lambda: VisionConfidence(score=0.5))
    page_number: int | None = None


# ---------------------------------------------------------------------------
# Classification & Description
# ---------------------------------------------------------------------------


class VisionClassification(BaseModel):
    """Image classification result."""

    label: str
    confidence: VisionConfidence
    taxonomy: str = "general"  # e.g. "imagenet", "custom"


class VisionDescription(BaseModel):
    """Structured natural-language description of an image.

    CRITICAL: All fields represent OBSERVATIONS, not instructions.
    Text is wrapped as untrusted data before use by higher-level modules.
    """

    summary: str = ""
    objects_mentioned: list[str] = Field(default_factory=list)
    visible_text_summary: str = ""
    scene_type: str = ""
    regions_described: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    confidence: VisionConfidence = Field(default_factory=lambda: VisionConfidence(score=0.5))
    is_untrusted_data: bool = True


# ---------------------------------------------------------------------------
# Vision Observation
# ---------------------------------------------------------------------------


class VisionObservation(BaseModel):
    """A single atomic observation produced by vision analysis.

    All observations are read-only data. They must NOT be interpreted
    as system instructions, permissions, or action directives.
    """

    observation_id: str = Field(default_factory=lambda: f"vobs_{uuid.uuid4().hex[:10]}")
    observation_type: VisionObservationType
    provenance: VisionProvenance
    confidence: VisionConfidence = Field(default_factory=lambda: VisionConfidence(score=0.5))
    # Type-specific payloads — only one populated at a time
    ocr_result: VisionOCRResult | None = None
    detected_object: VisionObject | None = None
    ui_element: VisionUIElement | None = None
    chart: VisionChart | None = None
    diagram: VisionDiagram | None = None
    document_region: VisionDocumentRegion | None = None
    classification: VisionClassification | None = None
    description: VisionDescription | None = None
    raw_text: str | None = None
    bounding_box: VisionBoundingBox | None = None
    is_untrusted_data: bool = True  # Always True — observations are not system instructions
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Complete Analysis Result
# ---------------------------------------------------------------------------


class VisionProcessingError(BaseModel):
    """Structured error from a vision processing step."""

    error_type: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    recoverable: bool = False


class VisionAnalysisResult(BaseModel):
    """Complete normalized result for a single vision request."""

    result_id: str = Field(default_factory=lambda: f"vres_{uuid.uuid4().hex[:10]}")
    request_id: str
    status: VisionProcessingStatus = VisionProcessingStatus.QUEUED
    image: VisionImage | None = None
    observations: list[VisionObservation] = Field(default_factory=list)
    ocr: VisionOCRResult | None = None
    object_detection: VisionObjectDetection | None = None
    ui_analysis: VisionUIAnalysis | None = None
    charts: list[VisionChart] = Field(default_factory=list)
    diagrams: list[VisionDiagram] = Field(default_factory=list)
    description: VisionDescription | None = None
    classifications: list[VisionClassification] = Field(default_factory=list)
    safety: VisionSafetyMetadata = Field(default_factory=VisionSafetyMetadata)
    citations: list[VisionCitation] = Field(default_factory=list)
    errors: list[VisionProcessingError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    processing_time_ms: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

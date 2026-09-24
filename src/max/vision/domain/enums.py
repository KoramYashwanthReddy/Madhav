"""Domain enums for Module 25 — Vision System."""

from enum import StrEnum


class VisionFormat(StrEnum):
    """Supported image/visual formats."""

    PNG = "PNG"
    JPEG = "JPEG"
    WEBP = "WEBP"
    BMP = "BMP"
    TIFF = "TIFF"
    GIF = "GIF"
    UNKNOWN = "UNKNOWN"


class VisionInputType(StrEnum):
    """Classification of the visual input source type."""

    FILE = "FILE"
    MEMORY_REFERENCE = "MEMORY_REFERENCE"
    SCREENSHOT = "SCREENSHOT"
    BROWSER_SCREENSHOT = "BROWSER_SCREENSHOT"
    DOCUMENT_PAGE = "DOCUMENT_PAGE"
    CAMERA_FRAME = "CAMERA_FRAME"
    BYTE_STREAM = "BYTE_STREAM"


class VisionSourceType(StrEnum):
    """Origin classification for where a visual input came from."""

    LOCAL_FILE = "LOCAL_FILE"
    FILESYSTEM_REFERENCE = "FILESYSTEM_REFERENCE"
    DOCUMENT_REFERENCE = "DOCUMENT_REFERENCE"
    SCREENSHOT_REFERENCE = "SCREENSHOT_REFERENCE"
    CAMERA_REFERENCE = "CAMERA_REFERENCE"
    TEMPORARY_REFERENCE = "TEMPORARY_REFERENCE"
    BYTE_STREAM = "BYTE_STREAM"


class VisionColorSpace(StrEnum):
    """Color space of the image."""

    RGB = "RGB"
    RGBA = "RGBA"
    GRAYSCALE = "GRAYSCALE"
    CMYK = "CMYK"
    YCbCr = "YCbCr"
    LAB = "LAB"
    UNKNOWN = "UNKNOWN"


class VisionCapability(StrEnum):
    """Capabilities that can be requested in a VisionRequest."""

    OCR = "OCR"
    OBJECT_DETECTION = "OBJECT_DETECTION"
    IMAGE_CLASSIFICATION = "IMAGE_CLASSIFICATION"
    IMAGE_DESCRIPTION = "IMAGE_DESCRIPTION"
    UI_ANALYSIS = "UI_ANALYSIS"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    CHART_ANALYSIS = "CHART_ANALYSIS"
    DIAGRAM_ANALYSIS = "DIAGRAM_ANALYSIS"
    SCENE_ANALYSIS = "SCENE_ANALYSIS"
    FACE_DETECTION = "FACE_DETECTION"
    TEXT_LOCALIZATION = "TEXT_LOCALIZATION"


class VisionObservationType(StrEnum):
    """Type of observation produced by a vision analysis step."""

    TEXT = "TEXT"
    OBJECT = "OBJECT"
    REGION = "REGION"
    UI_ELEMENT = "UI_ELEMENT"
    CHART = "CHART"
    DIAGRAM = "DIAGRAM"
    DOCUMENT_REGION = "DOCUMENT_REGION"
    FACE = "FACE"
    SCENE = "SCENE"
    CLASSIFICATION = "CLASSIFICATION"
    DESCRIPTION = "DESCRIPTION"


class VisionObjectClass(StrEnum):
    """Standard object class taxonomy for object detection results."""

    PERSON = "PERSON"
    FACE = "FACE"
    LAPTOP = "LAPTOP"
    PHONE = "PHONE"
    TABLET = "TABLET"
    MONITOR = "MONITOR"
    SCREEN = "SCREEN"
    KEYBOARD = "KEYBOARD"
    MOUSE = "MOUSE"
    CAR = "CAR"
    CHAIR = "CHAIR"
    TABLE = "TABLE"
    BOOK = "BOOK"
    PEN = "PEN"
    CUP = "CUP"
    BUTTON = "BUTTON"
    TEXT_REGION = "TEXT_REGION"
    ICON = "ICON"
    LOGO = "LOGO"
    CHART = "CHART"
    DIAGRAM = "DIAGRAM"
    DOCUMENT = "DOCUMENT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class VisionUIElementType(StrEnum):
    """UI element types detectable in screenshots."""

    BUTTON = "BUTTON"
    INPUT = "INPUT"
    TEXT_FIELD = "TEXT_FIELD"
    LABEL = "LABEL"
    LINK = "LINK"
    MENU = "MENU"
    MENU_ITEM = "MENU_ITEM"
    DIALOG = "DIALOG"
    CHECKBOX = "CHECKBOX"
    RADIO_BUTTON = "RADIO_BUTTON"
    TAB = "TAB"
    TAB_BAR = "TAB_BAR"
    CARD = "CARD"
    TABLE = "TABLE"
    TABLE_CELL = "TABLE_CELL"
    NAVIGATION = "NAVIGATION"
    ICON = "ICON"
    WINDOW = "WINDOW"
    PANEL = "PANEL"
    TOOLBAR = "TOOLBAR"
    STATUSBAR = "STATUSBAR"
    SCROLLBAR = "SCROLLBAR"
    DROPDOWN = "DROPDOWN"
    TOOLTIP = "TOOLTIP"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class VisionChartType(StrEnum):
    """Recognized chart/graph types."""

    BAR_CHART = "BAR_CHART"
    LINE_CHART = "LINE_CHART"
    PIE_CHART = "PIE_CHART"
    SCATTER_PLOT = "SCATTER_PLOT"
    AREA_CHART = "AREA_CHART"
    HISTOGRAM = "HISTOGRAM"
    HEATMAP = "HEATMAP"
    CANDLESTICK = "CANDLESTICK"
    GANTT = "GANTT"
    RADAR = "RADAR"
    TREEMAP = "TREEMAP"
    UNKNOWN = "UNKNOWN"


class VisionProcessingStatus(StrEnum):
    """Processing lifecycle states for a vision request."""

    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    PREPROCESSING = "PREPROCESSING"
    ANALYZING = "ANALYZING"
    POSTPROCESSING = "POSTPROCESSING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class VisionConfidenceLevel(StrEnum):
    """Qualitative confidence classification."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNCERTAIN = "UNCERTAIN"


class VisionModelCapability(StrEnum):
    """Capabilities declared by a vision model."""

    VISION = "VISION"
    OCR = "OCR"
    OBJECT_DETECTION = "OBJECT_DETECTION"
    MULTIMODAL = "MULTIMODAL"
    IMAGE_CLASSIFICATION = "IMAGE_CLASSIFICATION"
    UI_ANALYSIS = "UI_ANALYSIS"
    DOCUMENT_VISION = "DOCUMENT_VISION"
    CHART_ANALYSIS = "CHART_ANALYSIS"
    FACE_DETECTION = "FACE_DETECTION"


class VisionModelStatus(StrEnum):
    """Lifecycle status of a vision model."""

    AVAILABLE = "AVAILABLE"
    NOT_INSTALLED = "NOT_INSTALLED"
    LOADING = "LOADING"
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"

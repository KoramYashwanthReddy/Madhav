"""Domain exceptions for Module 25 — Vision System."""


class VisionError(Exception):
    """Base exception for all Vision System errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class VisionInputError(VisionError):
    """Raised when visual input is invalid, missing, or malformed."""


class UnsupportedImageFormatError(VisionInputError):
    """Raised when the image format is not supported by the Vision System."""


class ImageDecodeError(VisionInputError):
    """Raised when an image cannot be decoded (corrupted, truncated, invalid)."""


class ImageTooLargeError(VisionInputError):
    """Raised when an image exceeds configured size, dimension, or pixel limits."""


class VisionProviderError(VisionError):
    """Raised when a vision provider fails to process a request."""


class VisionModelUnavailableError(VisionProviderError):
    """Raised when the requested vision model is not available or not installed."""


class VisionProcessingTimeoutError(VisionError):
    """Raised when vision processing exceeds the configured timeout limit."""


class VisionProcessingCancelledError(VisionError):
    """Raised when vision processing is explicitly cancelled."""


class VisionSecurityError(VisionError):
    """Raised when a vision operation violates a security or permission boundary."""


class VisionPermissionError(VisionSecurityError):
    """Raised when a required permission is not granted for a vision operation."""


class OCRProcessingError(VisionError):
    """Raised when OCR processing fails on an image."""


class VisionOutputValidationError(VisionError):
    """Raised when provider output fails normalization or quality validation."""


class VisionNotFoundError(VisionError):
    """Raised when a referenced vision request or result cannot be found."""


class CameraPermissionError(VisionSecurityError):
    """Raised when camera access is attempted without explicit permission."""


class ScreenCapturePermissionError(VisionSecurityError):
    """Raised when screen capture is attempted without explicit permission."""

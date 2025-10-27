"""
Facial processing exceptions.
"""

from fastapi import HTTPException, status


class FacialProcessingException(HTTPException):
    """Base facial processing exception."""

    def __init__(self, detail: str, error_code: str = "FACIAL_PROCESSING_ERROR"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": detail, "error_code": error_code},
        )


class InvalidImageException(HTTPException):
    """Raised when image data is invalid."""

    def __init__(self, detail: str = "Invalid image data"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": detail, "error_code": "INVALID_IMAGE"},
        )


class InsufficientLandmarksException(HTTPException):
    """Raised when insufficient landmarks are provided."""

    def __init__(self, detail: str = "Insufficient landmarks provided"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": detail, "error_code": "INSUFFICIENT_LANDMARKS"},
        )


class JobNotFoundException(HTTPException):
    """Raised when processing job is not found."""

    def __init__(self, detail: str = "Processing job not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": detail, "error_code": "JOB_NOT_FOUND"},
        )


class ProcessingTimeoutException(HTTPException):
    """Raised when processing times out."""

    def __init__(self, detail: str = "Processing timeout"):
        super().__init__(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail={"detail": detail, "error_code": "PROCESSING_TIMEOUT"},
        )


class UnsupportedFormatException(HTTPException):
    """Raised when output format is not supported."""

    def __init__(self, detail: str = "Unsupported output format"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": detail, "error_code": "UNSUPPORTED_FORMAT"},
        )


class ProcessingError(HTTPException):
    """Raised when processing fails."""

    def __init__(self, detail: str = "Processing failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": detail, "error_code": "PROCESSING_ERROR"},
        )

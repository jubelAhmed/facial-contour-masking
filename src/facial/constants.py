"""
Facial processing constants and enums.
"""

from enum import Enum


class ProcessingStatus(str, Enum):
    """Processing status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OutputFormat(str, Enum):
    """Output format types."""
    SVG = "svg"
    PNG = "png"
    JSON = "json"


class RegionType(str, Enum):
    """Face region types."""
    FOREHEAD = "forehead"
    LEFT_EYE = "left_eye"
    RIGHT_EYE = "right_eye"
    NOSE = "nose"
    MOUTH = "mouth"
    LEFT_CHEEK = "left_cheek"
    RIGHT_CHEEK = "right_cheek"
    CHIN = "chin"

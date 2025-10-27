"""
Consolidated facial processing module.
Contains models, schemas, constants, exceptions, and core processing logic.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.sql import func

from src.core.models import Base

# ============================================================================
# CONSTANTS & ENUMS
# ============================================================================

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

# ============================================================================
# DATABASE MODELS
# ============================================================================

class ProcessingJob(Base):
    """Processing job model."""
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    status = Column(String(50), nullable=False, default=ProcessingStatus.PENDING.value)
    input_data = Column(Text)  # JSON string
    output_data = Column(Text)  # JSON string
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

class PerceptualHash(Base):
    """Perceptual hash cache model."""
    __tablename__ = "perceptual_hashes"
    
    id = Column(Integer, primary_key=True, index=True)
    hash_value = Column(String(255), unique=True, index=True, nullable=False)
    result_data = Column(Text)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())

class ProcessingMetrics(Base):
    """Processing metrics model."""
    __tablename__ = "processing_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), nullable=False, index=True)
    processing_time = Column(Float)  # seconds
    memory_usage = Column(Float)  # MB
    cpu_usage = Column(Float)  # percentage
    output_size = Column(Integer)  # bytes
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class LandmarkPoint(BaseModel):
    """Landmark point schema."""
    x: float
    y: float

class ProcessingRequest(BaseModel):
    """Processing request schema."""
    image_data: str = Field(..., description="Base64 encoded image")
    landmarks: List[LandmarkPoint] = Field(..., description="68 facial landmarks")
    output_format: OutputFormat = Field(OutputFormat.SVG, description="Output format")
    style: Optional[str] = Field("default", description="Style configuration")

class ProcessingResponse(BaseModel):
    """Processing response schema."""
    job_id: str
    status: ProcessingStatus
    message: str
    result: Optional[Dict[str, Any]] = None

class JobStatusResponse(BaseModel):
    """Job status response schema."""
    job_id: str
    status: ProcessingStatus
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# ============================================================================
# EXCEPTIONS
# ============================================================================

class FacialProcessingException(HTTPException):
    """Base facial processing exception."""
    
    def __init__(self, detail: str, error_code: str = "PROCESSING_ERROR"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "detail": detail,
                "error_code": error_code
            }
        )

class InvalidImageException(FacialProcessingException):
    """Raised when image is invalid."""
    
    def __init__(self, detail: str = "Invalid image format"):
        super().__init__(detail, "INVALID_IMAGE")

class InsufficientLandmarksException(FacialProcessingException):
    """Raised when landmarks are insufficient."""
    
    def __init__(self, detail: str = "Insufficient landmarks provided"):
        super().__init__(detail, "INSUFFICIENT_LANDMARKS")

class ProcessingTimeoutException(FacialProcessingException):
    """Raised when processing times out."""
    
    def __init__(self, detail: str = "Processing timeout"):
        super().__init__(detail, "PROCESSING_TIMEOUT")

class JobNotFoundException(HTTPException):
    """Raised when job is not found."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "detail": "Job not found",
                "error_code": "JOB_NOT_FOUND"
            }
        )

# ============================================================================
# STYLE CONFIGURATION
# ============================================================================

@dataclass
class RegionStyle:
    """Data class for region styling information."""
    stroke: str
    fill: str
    stroke_width: int = 2
    stroke_dasharray: Optional[str] = None
    font_size: int = 26
    text_color: str = "white"

class StyleConfig(ABC):
    """Abstract base class for style configuration strategies."""
    
    @abstractmethod
    def get_region_style(self, region_id: int) -> RegionStyle:
        """Get style configuration for a specific region."""
        pass
    
    @abstractmethod
    def get_default_style(self) -> RegionStyle:
        """Get default style configuration."""
        pass

class DefaultStyleConfig(StyleConfig):
    """Default style configuration."""
    
    def get_region_style(self, region_id: int) -> RegionStyle:
        """Get default style for region."""
        colors = {
            1: "#9D57A7",  # Main face - Purple
            2: "#FF6B6B",  # Forehead - Red
            3: "#4ECDC4",  # Left eye - Teal
            4: "#45B7D1",  # Right eye - Blue
            5: "#96CEB4",  # Nose - Green
            6: "#FFEAA7",  # Mouth - Yellow
            7: "#DDA0DD",  # Left cheek - Plum
            8: "#98D8C8",  # Right cheek - Mint
            9: "#F7DC6F"   # Chin - Gold
        }
        
        color = colors.get(region_id, "#9D57A7")
        return RegionStyle(
            stroke=color,
            fill=color,
            stroke_width=2,
            font_size=26,
            text_color="white"
        )
    
    def get_default_style(self) -> RegionStyle:
        """Get default style."""
        return RegionStyle(
            stroke="#9D57A7",
            fill="#9D57A7",
            stroke_width=2,
            font_size=26,
            text_color="white"
        )

class ColorfulStyleConfig(StyleConfig):
    """Colorful style configuration."""
    
    def get_region_style(self, region_id: int) -> RegionStyle:
        """Get colorful style for region."""
        colors = {
            1: "#FF6B6B",  # Main face - Red
            2: "#4ECDC4",  # Forehead - Teal
            3: "#45B7D1",  # Left eye - Blue
            4: "#96CEB4",  # Right eye - Green
            5: "#FFEAA7",  # Nose - Yellow
            6: "#DDA0DD",  # Mouth - Plum
            7: "#98D8C8",  # Left cheek - Mint
            8: "#F7DC6F",  # Right cheek - Gold
            9: "#FFB6C1"   # Chin - Pink
        }
        
        color = colors.get(region_id, "#FF6B6B")
        return RegionStyle(
            stroke=color,
            fill=color,
            stroke_width=3,
            font_size=28,
            text_color="white"
        )
    
    def get_default_style(self) -> RegionStyle:
        """Get default colorful style."""
        return RegionStyle(
            stroke="#FF6B6B",
            fill="#FF6B6B",
            stroke_width=3,
            font_size=28,
            text_color="white"
        )

class MinimalStyleConfig(StyleConfig):
    """Minimal style configuration."""
    
    def get_region_style(self, region_id: int) -> RegionStyle:
        """Get minimal style for region."""
        return RegionStyle(
            stroke="#333333",
            fill="none",
            stroke_width=1,
            stroke_dasharray="5,5",
            font_size=24,
            text_color="#666666"
        )
    
    def get_default_style(self) -> RegionStyle:
        """Get default minimal style."""
        return RegionStyle(
            stroke="#333333",
            fill="none",
            stroke_width=1,
            stroke_dasharray="5,5",
            font_size=24,
            text_color="#666666"
        )

class StyleConfigFactory:
    """Factory for creating style configurations."""
    
    _configs = {
        "default": DefaultStyleConfig,
        "colorful": ColorfulStyleConfig,
        "minimal": MinimalStyleConfig
    }
    
    @classmethod
    def create_style_config(cls, style_name: str) -> StyleConfig:
        """Create style configuration by name."""
        config_class = cls._configs.get(style_name, DefaultStyleConfig)
        return config_class()
    
    @classmethod
    def get_available_styles(cls) -> List[str]:
        """Get list of available style names."""
        return list(cls._configs.keys())

# ============================================================================
# CORE PROCESSING CLASSES
# ============================================================================

class FacialSegmentationProcessor:
    """Main facial segmentation processor."""
    
    def __init__(self, style_config: StyleConfig = None):
        self.style_config = style_config or DefaultStyleConfig()
        self.processing_cache = {}
    
    def process_image(self, image_data: str, landmarks: List[LandmarkPoint]) -> Dict[str, Any]:
        """Process facial image and return segmentation data."""
        try:
            # Validate input
            if not image_data:
                raise InvalidImageException("No image data provided")
            
            if len(landmarks) < 68:
                raise InsufficientLandmarksException("At least 68 landmarks required")
            
            # Process landmarks and generate contours
            contours = self._extract_contours(landmarks)
            
            # Generate output based on style
            result = {
                "contours": contours,
                "style": self.style_config.get_default_style().__dict__,
                "regions": self._get_region_info(contours)
            }
            
            return result
            
        except Exception as e:
            if isinstance(e, FacialProcessingException):
                raise
            raise FacialProcessingException(f"Processing failed: {str(e)}")
    
    def _extract_contours(self, landmarks: List[LandmarkPoint]) -> Dict[int, List[Tuple[float, float]]]:
        """Extract contours from landmarks."""
        # Simplified contour extraction
        contours = {}
        
        # Define region mappings (simplified)
        region_mappings = {
            1: list(range(0, 17)),  # Main face
            2: list(range(17, 22)), # Forehead
            3: list(range(36, 42)), # Left eye
            4: list(range(42, 48)), # Right eye
            5: list(range(27, 36)), # Nose
            6: list(range(48, 68)), # Mouth
            7: list(range(0, 5)),   # Left cheek
            8: list(range(12, 17)), # Right cheek
            9: list(range(6, 12))   # Chin
        }
        
        for region_id, landmark_indices in region_mappings.items():
            if all(i < len(landmarks) for i in landmark_indices):
                points = [(landmarks[i].x, landmarks[i].y) for i in landmark_indices]
                contours[region_id] = points
        
        return contours
    
    def _get_region_info(self, contours: Dict[int, List[Tuple[float, float]]]) -> Dict[str, Any]:
        """Get region information."""
        regions = {}
        for region_id, points in contours.items():
            if points:
                regions[f"region_{region_id}"] = {
                    "point_count": len(points),
                    "style": self.style_config.get_region_style(region_id).__dict__
                }
        return regions

# ============================================================================
# UTILITIES
# ============================================================================

def validate_image_data(image_data: str) -> bool:
    """Validate base64 image data."""
    try:
        import base64
        base64.b64decode(image_data)
        return True
    except Exception:
        return False

def calculate_region_area(points: List[Tuple[float, float]]) -> float:
    """Calculate area of a region from points."""
    if len(points) < 3:
        return 0.0
    
    # Simple shoelace formula
    area = 0.0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2.0

def get_region_center(points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Get center point of a region."""
    if not points:
        return (0.0, 0.0)
    
    x_sum = sum(point[0] for point in points)
    y_sum = sum(point[1] for point in points)
    return (x_sum / len(points), y_sum / len(points))

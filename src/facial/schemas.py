"""
Facial processing Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class LandmarkPoint(BaseModel):
    """Facial landmark point schema."""

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")

    model_config = ConfigDict(from_attributes=True)


class ProcessingRequest(BaseModel):
    """Facial processing request schema."""

    image_data: str = Field(..., description="Base64 encoded image data")
    landmarks: List[LandmarkPoint] = Field(
        ..., min_length=68, description="68 facial landmarks"
    )
    output_format: str = Field("svg", description="Output format (svg, png, json)")
    style: Optional[str] = Field(None, description="Processing style")

    @field_validator("landmarks")
    @classmethod
    def validate_landmarks(cls, v):
        if len(v) < 68:
            raise ValueError("At least 68 landmarks are required")
        return v

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v):
        allowed_formats = ["svg", "png", "json"]
        if v.lower() not in allowed_formats:
            raise ValueError(f"Output format must be one of: {allowed_formats}")
        return v.lower()


class ProcessingResponse(BaseModel):
    """Facial processing response schema."""

    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Response message")

    model_config = ConfigDict(from_attributes=True)


class JobStatusResponse(BaseModel):
    """Job status response schema."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current status")
    result: Optional[Dict[str, Any]] = Field(None, description="Processing result")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[datetime] = Field(None, description="Job creation time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")

    model_config = ConfigDict(from_attributes=True)


class ContourRegion(BaseModel):
    """Facial contour region schema."""

    region_id: str = Field(..., description="Region identifier")
    region_name: str = Field(..., description="Human-readable region name")
    contours: List[List[LandmarkPoint]] = Field(..., description="Contour points")
    style: Dict[str, Any] = Field(..., description="Visual style properties")

    model_config = ConfigDict(from_attributes=True)


class ProcessingResult(BaseModel):
    """Processing result schema."""

    job_id: str = Field(..., description="Job identifier")
    regions: List[ContourRegion] = Field(..., description="Processed regions")
    output_format: str = Field(..., description="Output format")
    style: str = Field(..., description="Applied style")
    processed_at: str = Field(..., description="Processing timestamp")

    model_config = ConfigDict(from_attributes=True)

"""
Facial processing database models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from src.shared.models import Base


class ProcessingStatus(str, Enum):
    """Processing job status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingJob(Base):
    """Processing job model."""

    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    input_data = Column(Text, nullable=False)
    output_data = Column(Text)
    status = Column(String(50), default="pending", nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "user_id": self.user_id,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


class PerceptualHash(Base):
    """Perceptual hash model for caching."""

    __tablename__ = "perceptual_hashes"

    id = Column(Integer, primary_key=True, index=True)
    hash_value = Column(String(255), unique=True, index=True, nullable=False)
    result_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert hash to dictionary."""
        return {
            "id": self.id,
            "hash_value": self.hash_value,
            "result_data": self.result_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed": (
                self.last_accessed.isoformat() if self.last_accessed else None
            ),
        }


class ProcessingMetrics(Base):
    """Processing metrics model."""

    __tablename__ = "processing_metrics"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), nullable=False, index=True)
    processing_time = Column(Float, nullable=False)
    memory_usage = Column(Float)
    cpu_usage = Column(Float)
    cache_hit = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "processing_time": self.processing_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "cache_hit": self.cache_hit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

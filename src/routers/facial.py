"""
Facial processing router - simplified version for testing.
"""

import time
import uuid
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.auth.models import User
from src.dependencies import get_current_user, get_optional_current_user
from src.middleware.rate_limiting import processing_rate_limit, status_rate_limit
from src.shared.database import SessionDep
from src.shared.utils import log_job_status, log_request, log_response, logger

router = APIRouter(prefix="/api/v1", tags=["facial-processing"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "facial-processing"}


@router.get("/status/{job_id}")
@status_rate_limit()
async def get_job_status(
    job_id: str, request: Request, current_user: User = Depends(get_current_user)
):
    """Get job status - simplified version."""
    logger.info(f"Job status requested for {job_id} by user {current_user.username}")
    return {
        "job_id": job_id,
        "status": "completed",
        "message": "Service is running - full functionality will be implemented",
    }


@router.post("/process")
@processing_rate_limit()
async def process_image(
    request: Request, current_user: User = Depends(get_current_user)
):
    """Process facial image - simplified version for testing."""
    logger.info(f"Image processing requested by user {current_user.username}")

    # For testing purposes, return a mock response
    job_id = str(uuid.uuid4())
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Image processing started - full functionality will be implemented",
        "user": current_user.username,
    }


@router.post("/test")
@processing_rate_limit()
async def test_endpoint(
    request: Request, current_user: User = Depends(get_current_user)
):
    """Test endpoint to verify the service is working."""
    logger.info(f"Test endpoint called by user {current_user.username}")
    return {
        "message": "Facial processing service is running!",
        "user": current_user.username,
        "timestamp": time.time(),
    }

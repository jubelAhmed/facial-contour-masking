"""
Facial processing router - simplified version for testing.
"""

import time
import uuid
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.auth.models import User
from src.dependencies import get_current_user, get_optional_current_user, get_facial_service
from src.facial.service import FacialProcessingService
from src.facial.schemas import ProcessingRequest, ProcessingResponse
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
    job_id: str, 
    request: Request, 
    current_user: User = Depends(get_current_user),
    facial_service: FacialProcessingService = Depends(get_facial_service)
):
    """Get job status using facial processing service."""
    logger.info(f"Job status requested for {job_id} by user {current_user.username}")
    
    try:
        job_status = await facial_service.get_job_status(job_id)
        return job_status
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job status"
        )


@router.post("/process", response_model=ProcessingResponse)
@processing_rate_limit()
async def process_image(
    processing_request: ProcessingRequest,
    request: Request, 
    current_user: User = Depends(get_current_user),
    facial_service: FacialProcessingService = Depends(get_facial_service)
):
    """Process facial image using facial processing service."""
    logger.info(f"Image processing requested by user {current_user.username}")

    try:
        # Create processing job using the service
        result = await facial_service.create_processing_job(
            user_id=current_user.id,
            image_data=processing_request.image_data,
            output_format=processing_request.output_format,
            options=processing_request.options
        )
        return result
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process image"
        )


@router.post("/test")
@processing_rate_limit()
async def test_endpoint(
    request: Request, 
    current_user: User = Depends(get_current_user),
    facial_service: FacialProcessingService = Depends(get_facial_service)
):
    """Test endpoint to verify the service is working."""
    logger.info(f"Test endpoint called by user {current_user.username}")
    
    # Test that the service is properly injected
    service_status = "Service properly injected" if facial_service else "Service not available"
    
    return {
        "message": "Facial processing service is running!",
        "user": current_user.username,
        "service_status": service_status,
        "timestamp": time.time(),
    }

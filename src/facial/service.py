"""
Facial processing service following Service Layer pattern.
Uses Repository pattern for data access (Dependency Injection).
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status

from src.facial.constants import OutputFormat, ProcessingStatus, RegionType
from src.facial.exceptions import (
    FacialProcessingException,
    InsufficientLandmarksException,
    InvalidImageException,
    JobNotFoundException,
)
from src.facial.models import PerceptualHash, ProcessingJob, ProcessingMetrics
from src.facial.repository import (
    IPerceptualHashRepository,
    IProcessingJobRepository,
    PerceptualHashRepository,
    ProcessingJobRepository,
)
from src.facial.schemas import (
    JobStatusResponse,
    LandmarkPoint,
    ProcessingRequest,
    ProcessingResponse,
)
from src.shared.database import SessionDep
from src.shared.utils import logger


class FacialProcessingService:
    """Facial processing service following Service Layer pattern."""

    def __init__(
        self,
        job_repository: IProcessingJobRepository,
        hash_repository: IPerceptualHashRepository,
    ):
        """Initialize facial processing service with repositories (Dependency Injection)."""
        self.job_repository = job_repository
        self.hash_repository = hash_repository
        # self.processor = FacialSegmentationProcessor()  # Removed missing dependency

    # ========== JOB MANAGEMENT METHODS ==========

    async def create_processing_job(
        self, user_id: int, request: ProcessingRequest
    ) -> ProcessingResponse:
        """Create a new facial processing job."""
        try:
            # Business logic validation
            await self._validate_processing_request(request)

            # Generate job ID
            job_id = str(uuid.uuid4())

            # Create job in database
            job = await self.job_repository.create_job(
                job_id=job_id,
                user_id=user_id,
                input_data=json.dumps(
                    {
                        "landmarks": [{"x": p.x, "y": p.y} for p in request.landmarks],
                        "output_format": request.output_format,
                        "style": request.style,
                    }
                ),
            )

            # Start processing asynchronously (in real app, use background tasks)
            await self._process_job_async(job_id, request)

            return ProcessingResponse(
                job_id=job_id,
                status="pending",
                message="Processing job created successfully",
            )

        except (InvalidImageException, InsufficientLandmarksException):
            raise
        except Exception as e:
            logger.error(f"Error creating processing job: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create processing job",
            )

    async def get_job_status(self, job_id: str) -> JobStatusResponse:
        """Get job status and result."""
        try:
            job = await self.job_repository.get_job_by_id(job_id)
            if not job:
                raise JobNotFoundException()

            result = None
            if job.output_data:
                result = json.loads(job.output_data)

            return JobStatusResponse(
                job_id=job_id,
                status=job.status,
                result=result,
                error=job.error_message,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )

        except JobNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get job status",
            )

    async def get_user_jobs(self, user_id: int) -> List[JobStatusResponse]:
        """Get all jobs for a user."""
        try:
            jobs = await self.job_repository.get_user_jobs(user_id)

            return [
                JobStatusResponse(
                    job_id=job.job_id,
                    status=job.status,
                    result=json.loads(job.output_data) if job.output_data else None,
                    error=job.error_message,
                    created_at=job.created_at,
                    completed_at=job.completed_at,
                )
                for job in jobs
            ]

        except Exception as e:
            logger.error(f"Error getting user jobs: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user jobs",
            )

    async def delete_job(self, job_id: str) -> bool:
        """Delete a processing job."""
        try:
            return await self.job_repository.delete_job(job_id)
        except Exception as e:
            logger.error(f"Error deleting job: {e}")
            return False

    # ========== PROCESSING METHODS ==========

    async def _process_job_async(self, job_id: str, request: ProcessingRequest) -> None:
        """Process job asynchronously (business logic)."""
        try:
            # Update job status to processing
            await self.job_repository.update_job_status(job_id, "processing")

            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = await self.hash_repository.get_by_hash(cache_key)

            if cached_result:
                # Use cached result
                result = json.loads(cached_result.result_data)
                await self.hash_repository.update_last_accessed(cache_key)
                logger.info(f"Using cached result for job {job_id}")
            else:
                # Process image
                result = await self._process_image(request)

                # Cache result
                await self.hash_repository.create_hash(cache_key, json.dumps(result))
                logger.info(f"Processed and cached result for job {job_id}")

            # Update job with result
            await self.job_repository.update_job_status(
                job_id, "completed", output_data=json.dumps(result)
            )

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            await self.job_repository.update_job_status(
                job_id, "failed", error_message=str(e)
            )

    async def _process_image(self, request: ProcessingRequest) -> Dict[str, Any]:
        """Process facial image (business logic)."""
        try:
            # Get style configuration
            style_config = StyleConfigFactory.create_style_config(
                request.style or "default"
            )
            self.processor.style_config = style_config

            # Process the image
            result = self.processor.process_image(request.image_data, request.landmarks)

            return {
                "contours": result["contours"],
                "style": result["style"],
                "regions": result["regions"],
                "output_format": request.output_format,
                "processed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise FacialProcessingException(f"Image processing failed: {str(e)}")

    # ========== CACHE MANAGEMENT METHODS ==========

    async def cleanup_old_cache(self, days: int = 30) -> int:
        """Clean up old cache entries."""
        try:
            return await self.hash_repository.cleanup_old_hashes(days)
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return 0

    # ========== PRIVATE HELPER METHODS ==========

    async def _validate_processing_request(self, request: ProcessingRequest) -> None:
        """Validate processing request (business logic)."""
        if not request.image_data:
            raise InvalidImageException("No image data provided")

        # Simple base64 validation
        try:
            import base64

            base64.b64decode(request.image_data, validate=True)
        except Exception:
            raise InvalidImageException("Invalid image format")

        if len(request.landmarks) < 68:
            raise InsufficientLandmarksException("At least 68 landmarks required")

    def _generate_cache_key(self, request: ProcessingRequest) -> str:
        """Generate cache key for request."""
        # Create hash from landmarks and style
        landmarks_str = json.dumps([{"x": p.x, "y": p.y} for p in request.landmarks])
        style_str = request.style or "default"

        content = f"{landmarks_str}:{style_str}"
        return hashlib.sha256(content.encode()).hexdigest()


# ========== DEPENDENCY INJECTION FUNCTIONS ==========


def get_processing_job_repository(session: SessionDep) -> IProcessingJobRepository:
    """Get processing job repository instance."""
    return ProcessingJobRepository(session)


def get_perceptual_hash_repository(session: SessionDep) -> IPerceptualHashRepository:
    """Get perceptual hash repository instance."""
    return PerceptualHashRepository(session)


def get_facial_processing_service(
    job_repo: IProcessingJobRepository = Depends(get_processing_job_repository),
    hash_repo: IPerceptualHashRepository = Depends(get_perceptual_hash_repository),
) -> FacialProcessingService:
    """Get facial processing service instance with dependency injection."""
    return FacialProcessingService(job_repo, hash_repo)

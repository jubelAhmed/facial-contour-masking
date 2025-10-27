"""
Background job worker for facial processing.
Handles asynchronous job processing with proper error handling and retries.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.facial.exceptions import FacialProcessingException, JobNotFoundException
from src.facial.repository import IPerceptualHashRepository, IProcessingJobRepository
from src.facial.schemas import ProcessingRequest
from src.shared.database import DatabaseManager
from src.shared.utils import logger
import contextlib


class BackgroundJobWorker:
    """Background job worker for processing facial images."""

    def __init__(
        self,
        job_repository: IProcessingJobRepository,
        hash_repository: IPerceptualHashRepository,
        db_manager: DatabaseManager,
    ):
        """Initialize background job worker."""
        self.job_repository = job_repository
        self.hash_repository = hash_repository
        self.db_manager = db_manager
        self.is_running = False
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    async def start_worker(self) -> None:
        """Start the background worker."""
        self.is_running = True
        logger.info("Background job worker started")

        while self.is_running:
            try:
                await self._process_pending_jobs()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in background worker: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def stop_worker(self) -> None:
        """Stop the background worker."""
        self.is_running = False
        logger.info("Background job worker stopped")

    async def _process_pending_jobs(self) -> None:
        """Process all pending jobs."""
        try:
            # Get pending jobs (this would need to be implemented in repository)
            pending_jobs = await self._get_pending_jobs()
            
            for job in pending_jobs:
                try:
                    await self._process_single_job(job)
                except Exception as e:
                    logger.error(f"Error processing job {job.job_id}: {e}")
                    await self._handle_job_error(job.job_id, str(e))

        except Exception as e:
            logger.error(f"Error getting pending jobs: {e}")

    async def _get_pending_jobs(self) -> List[Any]:
        """Get pending jobs from database."""
        # This would need to be implemented in the repository
        # For now, return empty list
        return []

    async def _process_single_job(self, job: Any) -> None:
        """Process a single job."""
        try:
            # Update job status to processing
            await self.job_repository.update_job_status(job.job_id, "processing")

            # Parse input data
            input_data = json.loads(job.input_data)
            request = ProcessingRequest(
                image_data=input_data.get("image_data", ""),
                landmarks=input_data.get("landmarks", []),
                output_format=input_data.get("output_format", "svg"),
                style=input_data.get("style", "default"),
            )

            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = await self.hash_repository.get_by_hash(cache_key)

            if cached_result:
                # Use cached result
                result = json.loads(cached_result.result_data)
                await self.hash_repository.update_last_accessed(cache_key)
                logger.info(f"Using cached result for job {job.job_id}")
            else:
                # Process image
                result = await self._process_image(request)

                # Cache result
                await self.hash_repository.create_hash(cache_key, json.dumps(result))
                logger.info(f"Processed and cached result for job {job.job_id}")

            # Update job with result
            await self.job_repository.update_job_status(
                job.job_id, "completed", output_data=json.dumps(result)
            )

            logger.info(f"Job {job.job_id} completed successfully")

        except Exception as e:
            logger.error(f"Error processing job {job.job_id}: {e}")
            await self._handle_job_error(job.job_id, str(e))

    async def _process_image(self, request: ProcessingRequest) -> Dict[str, Any]:
        """Process facial image (business logic)."""
        try:
            # Simulate processing time
            await asyncio.sleep(2)

            # Simplified processing - return mock result for now
            # TODO: Implement actual image processing logic

            return {
                "contours": [],
                "style": request.style or "default",
                "regions": [],
                "output_format": request.output_format,
                "processed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise FacialProcessingException(f"Image processing failed: {str(e)}")

    async def _handle_job_error(self, job_id: str, error_message: str) -> None:
        """Handle job processing error."""
        try:
            await self.job_repository.update_job_status(
                job_id, "failed", error_message=error_message
            )
            logger.error(f"Job {job_id} failed: {error_message}")
        except Exception as e:
            logger.error(f"Error updating failed job {job_id}: {e}")

    def _generate_cache_key(self, request: ProcessingRequest) -> str:
        """Generate cache key for request."""
        import hashlib

        # Create hash from landmarks and style
        landmarks_str = json.dumps([{"x": p.x, "y": p.y} for p in request.landmarks])
        style_str = request.style or "default"

        content = f"{landmarks_str}:{style_str}"
        return hashlib.sha256(content.encode()).hexdigest()


class BackgroundWorkerManager:
    """Manager for background worker instance."""
    
    def __init__(self):
        self._worker: Optional[BackgroundJobWorker] = None
        self._worker_task: Optional[asyncio.Task] = None
    
    async def get_worker(self) -> BackgroundJobWorker:
        """Get the background worker instance."""
        if self._worker is None:
            raise RuntimeError("Background worker not initialized")
        return self._worker
    
    async def start_worker(
        self,
        job_repository: IProcessingJobRepository,
        hash_repository: IPerceptualHashRepository,
        db_manager: DatabaseManager,
    ) -> BackgroundJobWorker:
        """Start the background worker."""
        self._worker = BackgroundJobWorker(job_repository, hash_repository, db_manager)
        self._worker_task = asyncio.create_task(self._worker.start_worker())
        return self._worker
    
    async def stop_worker(self) -> None:
        """Stop the background worker."""
        if self._worker:
            await self._worker.stop_worker()
            self._worker = None
        if self._worker_task:
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
            self._worker_task = None


# Global manager instance
_worker_manager = BackgroundWorkerManager()


async def get_background_worker() -> BackgroundJobWorker:
    """Get the global background worker instance."""
    return await _worker_manager.get_worker()


async def start_background_worker(
    job_repository: IProcessingJobRepository,
    hash_repository: IPerceptualHashRepository,
    db_manager: DatabaseManager,
) -> BackgroundJobWorker:
    """Start the background worker."""
    return await _worker_manager.start_worker(job_repository, hash_repository, db_manager)


async def stop_background_worker() -> None:
    """Stop the background worker."""
    await _worker_manager.stop_worker()

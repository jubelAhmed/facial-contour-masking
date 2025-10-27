"""
Facial processing repository following DAO pattern.
Implements data access operations for ProcessingJob and related entities.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.facial.models import PerceptualHash, ProcessingJob, ProcessingMetrics
from src.facial.schemas import LandmarkPoint
from src.shared.utils import logger


class IProcessingJobRepository(ABC):
    """Interface for ProcessingJob repository operations."""

    @abstractmethod
    async def create_job(
        self, job_id: str, user_id: int, input_data: str
    ) -> ProcessingJob:
        """Create new processing job."""
        pass

    @abstractmethod
    async def get_job_by_id(self, job_id: str) -> Optional[ProcessingJob]:
        """Get job by ID."""
        pass

    @abstractmethod
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        output_data: str = None,
        error_message: str = None,
    ) -> bool:
        """Update job status."""
        pass

    @abstractmethod
    async def get_user_jobs(self, user_id: int) -> List[ProcessingJob]:
        """Get all jobs for a user."""
        pass

    @abstractmethod
    async def delete_job(self, job_id: str) -> bool:
        """Delete job."""
        pass


class ProcessingJobRepository(IProcessingJobRepository):
    """Concrete implementation of ProcessingJob repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_job(
        self, job_id: str, user_id: int, input_data: str
    ) -> ProcessingJob:
        """Create new processing job."""
        try:
            job = ProcessingJob(
                job_id=job_id, user_id=user_id, input_data=input_data, status="pending"
            )
            self.session.add(job)
            await self.session.commit()
            await self.session.refresh(job)
            logger.info(f"Processing job created: {job_id}")
            return job
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating processing job: {e}")
            raise

    async def get_job_by_id(self, job_id: str) -> Optional[ProcessingJob]:
        """Get job by ID."""
        try:
            result = await self.session.execute(
                select(ProcessingJob).where(ProcessingJob.job_id == job_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting job by ID {job_id}: {e}")
            return None

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        output_data: str = None,
        error_message: str = None,
    ) -> bool:
        """Update job status."""
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow()}

            if output_data:
                update_data["output_data"] = output_data
            if error_message:
                update_data["error_message"] = error_message
            if status == "completed":
                update_data["completed_at"] = datetime.utcnow()

            await self.session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.job_id == job_id)
                .values(**update_data)
            )
            await self.session.commit()
            logger.info(f"Job {job_id} status updated to {status}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating job status: {e}")
            return False

    async def get_user_jobs(self, user_id: int) -> List[ProcessingJob]:
        """Get all jobs for a user."""
        try:
            result = await self.session.execute(
                select(ProcessingJob)
                .where(ProcessingJob.user_id == user_id)
                .order_by(ProcessingJob.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting user jobs: {e}")
            return []

    async def delete_job(self, job_id: str) -> bool:
        """Delete job."""
        try:
            await self.session.execute(
                delete(ProcessingJob).where(ProcessingJob.job_id == job_id)
            )
            await self.session.commit()
            logger.info(f"Job {job_id} deleted")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting job: {e}")
            return False


class IPerceptualHashRepository(ABC):
    """Interface for PerceptualHash repository operations."""

    @abstractmethod
    async def create_hash(self, hash_value: str, result_data: str) -> PerceptualHash:
        """Create perceptual hash entry."""
        pass

    @abstractmethod
    async def get_by_hash(self, hash_value: str) -> Optional[PerceptualHash]:
        """Get hash by value."""
        pass

    @abstractmethod
    async def update_last_accessed(self, hash_value: str) -> bool:
        """Update last accessed time."""
        pass

    @abstractmethod
    async def cleanup_old_hashes(self, days: int = 30) -> int:
        """Clean up old hash entries."""
        pass


class PerceptualHashRepository(IPerceptualHashRepository):
    """Concrete implementation of PerceptualHash repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_hash(self, hash_value: str, result_data: str) -> PerceptualHash:
        """Create perceptual hash entry."""
        try:
            hash_entry = PerceptualHash(hash_value=hash_value, result_data=result_data)
            self.session.add(hash_entry)
            await self.session.commit()
            await self.session.refresh(hash_entry)
            logger.info(f"Perceptual hash created: {hash_value[:16]}...")
            return hash_entry
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating perceptual hash: {e}")
            raise

    async def get_by_hash(self, hash_value: str) -> Optional[PerceptualHash]:
        """Get hash by value."""
        try:
            result = await self.session.execute(
                select(PerceptualHash).where(PerceptualHash.hash_value == hash_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting hash by value: {e}")
            return None

    async def update_last_accessed(self, hash_value: str) -> bool:
        """Update last accessed time."""
        try:
            await self.session.execute(
                update(PerceptualHash)
                .where(PerceptualHash.hash_value == hash_value)
                .values(last_accessed=datetime.utcnow())
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating last accessed: {e}")
            return False

    async def cleanup_old_hashes(self, days: int = 30) -> int:
        """Clean up old hash entries."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = await self.session.execute(
                delete(PerceptualHash).where(PerceptualHash.last_accessed < cutoff_date)
            )
            await self.session.commit()
            logger.info(f"Cleaned up {result.rowcount} old hash entries")
            return result.rowcount
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error cleaning up old hashes: {e}")
            return 0

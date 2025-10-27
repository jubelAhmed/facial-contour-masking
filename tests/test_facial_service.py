"""Test facial processing service functionality."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
import uuid

from fastapi import HTTPException
from src.facial.service import FacialProcessingService
from src.facial.schemas import ProcessingRequest, LandmarkPoint, ProcessingResponse
from src.facial.models import ProcessingJob, ProcessingStatus
from src.facial.exceptions import (
    FacialProcessingException,
    InvalidImageException,
    InsufficientLandmarksException,
    JobNotFoundException,
)


class TestFacialProcessingService:
    """Test FacialProcessingService functionality."""

    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories for testing."""
        mock_job_repo = AsyncMock()
        mock_hash_repo = AsyncMock()
        return mock_job_repo, mock_hash_repo

    @pytest.fixture
    def service(self, mock_repositories):
        """Create service instance with mocked dependencies."""
        mock_job_repo, mock_hash_repo = mock_repositories
        return FacialProcessingService(mock_job_repo, mock_hash_repo)

    @pytest.fixture
    def sample_request(self):
        """Create sample processing request."""
        landmarks = [LandmarkPoint(x=100.0 + i, y=200.0 + i) for i in range(68)]
        return ProcessingRequest(
            image_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            landmarks=landmarks,
            output_format="svg",
            style="default",
        )

    def test_service_initialization(self, service):
        """Test service can be initialized."""
        assert service is not None
        assert hasattr(service, "create_processing_job")
        assert hasattr(service, "get_job_status")

    @pytest.mark.asyncio
    async def test_process_image_creates_job(
        self, service, sample_request, mock_repositories
    ):
        """Test create_processing_job creates a processing job."""
        mock_job_repo, mock_hash_repo = mock_repositories

        # Mock job creation
        mock_job = ProcessingJob(
            id=1, status=ProcessingStatus.PROCESSING, created_at=datetime.now()
        )
        mock_job_repo.create_job.return_value = mock_job

        result = await service.create_processing_job(1, sample_request)

        assert result is not None
        assert hasattr(result, "job_id")
        assert result.job_id is not None  # Service generates its own job_id
        mock_job_repo.create_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_image_validates_landmarks(self, service, mock_repositories):
        """Test create_processing_job validates landmark count."""
        mock_job_repo, mock_hash_repo = mock_repositories

        # Create request with insufficient landmarks - this will fail at validation
        insufficient_landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(10)]

        with pytest.raises(Exception):  # Pydantic validation error
            invalid_request = ProcessingRequest(
                image_data="test_image",
                landmarks=insufficient_landmarks,
                output_format="svg",
            )

    @pytest.mark.asyncio
    async def test_process_image_validates_image(self, service, mock_repositories):
        """Test create_processing_job validates image data."""
        mock_job_repo, mock_hash_repo = mock_repositories

        # Create request with invalid image data
        invalid_request = ProcessingRequest(
            image_data="invalid_base64_data!!!",
            landmarks=[LandmarkPoint(x=100.0, y=200.0) for _ in range(68)],
            output_format="svg",
        )

        # This will be handled by the service's validation
        with pytest.raises(Exception):  # Will be caught by service validation
            await service.create_processing_job(1, invalid_request)

    @pytest.mark.asyncio
    async def test_get_job_status_found(self, service, mock_repositories):
        """Test get_job_status returns job when found."""
        mock_job_repo, mock_hash_repo = mock_repositories

        job_id = str(uuid.uuid4())
        mock_job = ProcessingJob(
            id=job_id,
            status=ProcessingStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
        )
        mock_job.output_data = '{"result": "test"}'
        mock_job_repo.get_job_by_id.return_value = mock_job

        result = await service.get_job_status(job_id)

        assert result is not None
        assert result.job_id == job_id
        assert result.status == ProcessingStatus.COMPLETED
        mock_job_repo.get_job_by_id.assert_called_once_with(job_id)

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, service, mock_repositories):
        """Test get_job_status raises exception when job not found."""
        mock_job_repo, mock_hash_repo = mock_repositories

        job_id = str(uuid.uuid4())
        mock_job_repo.get_job_by_id.return_value = None

        with pytest.raises(JobNotFoundException):
            await service.get_job_status(job_id)

    @pytest.mark.asyncio
    async def test_process_image_handles_processing_error(
        self, service, sample_request, mock_repositories
    ):
        """Test create_processing_job handles processing errors gracefully."""
        mock_job_repo, mock_hash_repo = mock_repositories

        # Mock job creation to raise an exception
        mock_job_repo.create_job.side_effect = Exception("Database error")

        with pytest.raises(Exception):  # HTTPException from service
            await service.create_processing_job(1, sample_request)

    def test_service_handles_different_output_formats(self, service, mock_repositories):
        """Test service handles different output formats."""
        mock_job_repo, mock_hash_repo = mock_repositories

        # Test with different output formats
        formats = ["svg", "png", "json"]

        for format_type in formats:
            landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(68)]
            request = ProcessingRequest(
                image_data="test_image", landmarks=landmarks, output_format=format_type
            )

            # Should not raise validation error for valid formats
            assert request.output_format == format_type

    @pytest.mark.asyncio
    async def test_service_handles_optional_style(self, service, mock_repositories):
        """Test service handles optional style parameter."""
        mock_job_repo, mock_hash_repo = mock_repositories

        landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(68)]
        request_with_style = ProcessingRequest(
            image_data="test_image",
            landmarks=landmarks,
            output_format="svg",
            style="artistic",
        )

        # Should accept optional style parameter
        assert request_with_style.style == "artistic"

        request_without_style = ProcessingRequest(
            image_data="test_image", landmarks=landmarks, output_format="svg"
        )

        # Should handle missing style parameter
        assert request_without_style.style is None


class TestProcessingJobModel:
    """Test ProcessingJob model functionality."""

    def test_processing_job_creation(self):
        """Test ProcessingJob can be created."""
        job_id = str(uuid.uuid4())
        job = ProcessingJob(
            id=job_id, status=ProcessingStatus.PROCESSING, created_at=datetime.now()
        )

        assert job.id == job_id
        assert job.status == ProcessingStatus.PROCESSING
        assert job.created_at is not None

    def test_processing_job_status_transitions(self):
        """Test ProcessingJob status transitions."""
        job_id = str(uuid.uuid4())
        job = ProcessingJob(
            id=job_id, status=ProcessingStatus.PROCESSING, created_at=datetime.now()
        )

        # Should be able to update status
        job.status = ProcessingStatus.COMPLETED
        job.completed_at = datetime.now()

        assert job.status == ProcessingStatus.COMPLETED
        assert job.completed_at is not None

    def test_processing_job_serialization(self):
        """Test ProcessingJob can be serialized."""
        job_id = str(uuid.uuid4())
        job = ProcessingJob(
            id=job_id, status=ProcessingStatus.PROCESSING, created_at=datetime.now()
        )

        # Should be serializable to dict
        job_dict = job.to_dict()
        assert job_dict["id"] == job_id
        assert job_dict["status"] == ProcessingStatus.PROCESSING


class TestFacialProcessingExceptions:
    """Test facial processing exceptions."""

    def test_facial_processing_exception(self):
        """Test FacialProcessingException can be created."""
        exception = FacialProcessingException("Test error")
        assert "Test error" in str(exception)
        assert isinstance(exception, Exception)

    def test_invalid_image_exception(self):
        """Test InvalidImageException can be created."""
        exception = InvalidImageException("Invalid image data")
        assert "Invalid image data" in str(exception)
        assert isinstance(exception, HTTPException)

    def test_insufficient_landmarks_exception(self):
        """Test InsufficientLandmarksException can be created."""
        exception = InsufficientLandmarksException("Not enough landmarks")
        assert "Not enough landmarks" in str(exception)
        assert isinstance(exception, HTTPException)

    def test_job_not_found_exception(self):
        """Test JobNotFoundException can be created."""
        exception = JobNotFoundException("Job not found")
        assert "Job not found" in str(exception)
        assert isinstance(exception, HTTPException)


class TestProcessingRequestSchema:
    """Test ProcessingRequest schema validation."""

    def test_valid_processing_request(self):
        """Test valid ProcessingRequest creation."""
        landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(68)]
        request = ProcessingRequest(
            image_data="test_image_data",
            landmarks=landmarks,
            output_format="svg",
            style="default",
        )

        assert request.image_data == "test_image_data"
        assert len(request.landmarks) == 68
        assert request.output_format == "svg"
        assert request.style == "default"

    def test_processing_request_validation_landmarks(self):
        """Test ProcessingRequest validates landmark count."""
        # Test with insufficient landmarks
        insufficient_landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(10)]

        with pytest.raises(ValueError):
            ProcessingRequest(
                image_data="test_image",
                landmarks=insufficient_landmarks,
                output_format="svg",
            )

    def test_processing_request_validation_output_format(self):
        """Test ProcessingRequest validates output format."""
        landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(68)]

        # Test with invalid output format
        with pytest.raises(ValueError):
            ProcessingRequest(
                image_data="test_image",
                landmarks=landmarks,
                output_format="invalid_format",
            )

    def test_processing_request_optional_style(self):
        """Test ProcessingRequest handles optional style."""
        landmarks = [LandmarkPoint(x=100.0, y=200.0) for _ in range(68)]

        # Test without style
        request_no_style = ProcessingRequest(
            image_data="test_image", landmarks=landmarks, output_format="svg"
        )
        assert request_no_style.style is None

        # Test with style
        request_with_style = ProcessingRequest(
            image_data="test_image",
            landmarks=landmarks,
            output_format="svg",
            style="artistic",
        )
        assert request_with_style.style == "artistic"

"""
Test configuration and fixtures.
"""

import os
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# Set test environment variables before importing the app
os.environ["TESTING"] = "true"
os.environ["DB_USE_DATABASE"] = "true"  # Enable database for tests
os.environ["AUTH_SECRET_KEY"] = "test-secret-key"
os.environ["AUTH_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["AUTH_REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["AUTH_ALGORITHM"] = "HS256"

# Import test database fixtures
from tests.test_database import test_engine, test_session, test_db_manager

@pytest.fixture(scope="session")
def client():
    """Test client fixture with test database."""
    # Override the database manager with test database
    with patch("src.shared.database.db_manager") as mock_db_manager:
        # This will be replaced by the test_db_manager fixture in individual tests
        from src.main import app
        return TestClient(app)

@pytest.fixture
async def app_with_test_db(test_db_manager):
    """App fixture with test database."""
    # Override the global database manager
    with patch("src.shared.database.db_manager", test_db_manager):
        from src.main import app
        yield app

@pytest.fixture
def client_with_test_db(app_with_test_db):
    """Test client with test database."""
    return TestClient(app_with_test_db)

@pytest.fixture
def mock_auth_service():
    """Mock auth service fixture."""
    mock_service = AsyncMock()
    mock_user = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False
    }
    mock_service.create_user = AsyncMock(return_value=mock_user)
    mock_service.authenticate_user = AsyncMock(return_value=mock_user)
    mock_service.create_access_token = AsyncMock(return_value="mock_access_token")
    mock_service.create_refresh_token = AsyncMock(return_value="mock_refresh_token")
    return mock_service

@pytest.fixture
def mock_facial_service():
    """Mock facial service fixture."""
    mock_service = AsyncMock()
    mock_response = {
        "job_id": "test-job-123",
        "status": "pending",
        "message": "Processing job created successfully"
    }
    mock_service.create_processing_job = AsyncMock(return_value=mock_response)
    mock_service.get_job_status = AsyncMock(return_value=mock_response)
    return mock_service
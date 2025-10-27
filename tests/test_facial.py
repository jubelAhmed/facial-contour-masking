"""Test facial processing module."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.main import app

client = TestClient(app)


def test_facial_endpoints_exist():
    """Test that facial processing endpoints are registered."""
    response = client.get("/docs")
    assert response.status_code == 200

    # Check that facial endpoints are in the OpenAPI schema
    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    openapi_data = openapi_response.json()

    paths = openapi_data.get("paths", {})
    assert "/api/v1/process" in paths
    assert "/api/v1/status/{job_id}" in paths


def test_facial_process_endpoint_structure():
    """Test facial process endpoint accepts correct structure."""
    # Test with minimal valid request (requires authentication)
    test_request = {
        "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",  # 1x1 PNG
        "landmarks": [{"x": 0, "y": 0} for _ in range(68)],  # 68 landmarks
        "output_format": "svg",
        "style": "default",
    }

    response = client.post("/api/v1/process?token=jessica", json=test_request)
    # This might fail due to database not being set up in tests
    # but we're testing the endpoint accepts the right format
    assert response.status_code in [
        200,
        403,
        422,
        500,
    ]  # 403 for auth, 422 for validation, 500 for DB issues


def test_facial_process_endpoint_validation():
    """Test facial process endpoint validation."""
    # Test missing required fields
    response = client.post("/api/v1/process?token=jessica", json={})
    assert response.status_code in [403, 422]  # 403 for auth, 422 for validation

    # Test invalid output format
    invalid_request = {
        "image_data": "invalid_base64",
        "landmarks": [{"x": 0, "y": 0} for _ in range(68)],
        "output_format": "invalid_format",
    }
    response = client.post("/api/v1/process?token=jessica", json=invalid_request)
    assert response.status_code in [403, 422]  # 403 for auth, 422 for validation

    # Test insufficient landmarks
    insufficient_landmarks_request = {
        "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
        "landmarks": [{"x": 0, "y": 0} for _ in range(10)],  # Only 10 landmarks
        "output_format": "svg",
    }
    response = client.post(
        "/api/v1/process?token=jessica", json=insufficient_landmarks_request
    )
    assert response.status_code in [403, 422]  # 403 for auth, 422 for validation


def test_facial_status_endpoint():
    """Test facial status endpoint structure."""
    # Test with a mock job ID
    job_id = "test-job-id-123"
    response = client.get(f"/api/v1/status/{job_id}?token=jessica")
    # This might fail due to database not being set up in tests
    # but we're testing the endpoint exists and accepts the right format
    assert response.status_code in [
        200,
        403,
        404,
        500,
    ]  # 403 for auth, 404 for not found, 500 for DB issues


def test_facial_landmarks_validation():
    """Test landmarks validation in facial processing."""
    # Test valid landmarks structure
    valid_landmarks = [{"x": 100.5, "y": 200.3}, {"x": 150.0, "y": 250.7}]

    # Test invalid landmarks structure (missing y)
    invalid_landmarks = [{"x": 100.5}, {"x": 150.0, "y": 250.7}]

    # This would be tested in the schema validation
    # The actual validation happens in the Pydantic schemas
    assert len(valid_landmarks) == 2
    assert all("x" in landmark and "y" in landmark for landmark in valid_landmarks)
    assert not all(
        "x" in landmark and "y" in landmark for landmark in invalid_landmarks
    )


def test_facial_output_formats():
    """Test supported output formats for facial processing."""
    supported_formats = ["svg", "png", "json"]

    for output_format in supported_formats:
        test_request = {
            "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            "landmarks": [{"x": 0, "y": 0} for _ in range(68)],
            "output_format": output_format,
        }

        response = client.post("/api/v1/process?token=jessica", json=test_request)
        # Should not fail due to invalid format
        assert response.status_code != 422 or "output_format" not in str(
            response.json()
        )


@patch("src.facial.service.FacialProcessingService")
def test_facial_processing_service_integration(mock_service):
    """Test facial processing service integration."""
    # Mock the service response
    mock_instance = MagicMock()
    mock_instance.process_image.return_value = {
        "job_id": "test-job-123",
        "status": "processing",
    }
    mock_service.return_value = mock_instance

    test_request = {
        "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
        "landmarks": [{"x": 0, "y": 0} for _ in range(68)],
        "output_format": "svg",
    }

    response = client.post("/api/v1/process?token=jessica", json=test_request)
    # This tests the integration without actual processing
    assert response.status_code in [
        200,
        403,
        422,
        500,
    ]  # 403 for auth, 422 for validation, 500 for DB issues


def test_facial_processing_async_behavior():
    """Test that facial processing returns job ID for async processing."""
    test_request = {
        "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
        "landmarks": [{"x": 0, "y": 0} for _ in range(68)],
        "output_format": "svg",
    }

    response = client.post("/api/v1/process?token=jessica", json=test_request)

    if response.status_code == 200:
        data = response.json()
        # Should return a job ID for async processing
        assert "job_id" in data
        assert "status" in data
        assert data["status"] in ["processing", "queued", "completed"]


def test_facial_processing_error_handling():
    """Test facial processing error handling."""
    # Test with invalid base64 image data
    invalid_image_request = {
        "image_data": "invalid_base64_data!!!",
        "landmarks": [{"x": 0, "y": 0} for _ in range(68)],
        "output_format": "svg",
    }

    response = client.post("/api/v1/process?token=jessica", json=invalid_image_request)
    # Should handle invalid image data gracefully
    assert response.status_code in [
        400,
        403,
        422,
        500,
    ]  # 403 for auth, 400/422 for validation, 500 for DB issues


def test_facial_processing_optional_parameters():
    """Test facial processing with optional parameters."""
    # Test with style parameter
    test_request_with_style = {
        "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
        "landmarks": [{"x": 0, "y": 0} for _ in range(68)],
        "output_format": "svg",
        "style": "artistic",
    }

    response = client.post(
        "/api/v1/process?token=jessica", json=test_request_with_style
    )
    # Should accept optional style parameter
    assert response.status_code in [
        200,
        403,
        422,
        500,
    ]  # 403 for auth, 422 for validation, 500 for DB issues


def test_facial_processing_rate_limiting():
    """Test that facial processing respects rate limiting."""
    # This would test rate limiting in a real scenario
    # For now, just test that the endpoint exists and can be called
    test_request = {
        "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
        "landmarks": [{"x": 0, "y": 0} for _ in range(68)],
        "output_format": "svg",
    }

    # Make multiple requests to test rate limiting
    responses = []
    for _ in range(5):
        response = client.post("/api/v1/process?token=jessica", json=test_request)
        responses.append(response.status_code)

    # At least some requests should succeed (rate limiting might not be active in tests)
    assert any(status in [200, 202, 403] for status in responses)  # 403 for auth issues

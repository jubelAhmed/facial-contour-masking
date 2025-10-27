"""Test main application module."""

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns correct response."""
    response = client.get("/?token=jessica")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "service" in data
    assert "version" in data
    assert "status" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health?token=jessica")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "database" in data
    assert "timestamp" in data


def test_docs_endpoint():
    """Test that docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_endpoint():
    """Test that OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data

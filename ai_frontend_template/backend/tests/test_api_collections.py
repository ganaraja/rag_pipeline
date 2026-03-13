"""
Integration tests for collection management endpoints.

These tests demonstrate how to test the reusable collection endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app, qdrant_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_collections():
    """Clean up test collections before each test."""
    yield
    # Cleanup after test
    try:
        collections = qdrant_manager.list_collections()
        for col in collections:
            if col.startswith("test-"):
                qdrant_manager.delete_collection(col)
    except:
        pass


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_collections_empty():
    """Test listing collections when none exist."""
    response = client.get("/api/collections")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_collection():
    """Test creating a new collection."""
    response = client.post(
        "/api/collections",
        json={"collection_name": "test-collection"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["collection_name"] == "test-collection"


def test_create_collection_duplicate():
    """Test creating a duplicate collection fails."""
    # Create first time
    client.post("/api/collections", json={"collection_name": "test-dup"})
    
    # Try to create again
    response = client.post("/api/collections", json={"collection_name": "test-dup"})
    assert response.status_code == 409


def test_create_collection_empty_name():
    """Test creating collection with empty name fails."""
    response = client.post("/api/collections", json={"collection_name": ""})
    assert response.status_code in [400, 422]  # 422 for Pydantic validation, 400 for custom validation


def test_delete_collection():
    """Test deleting a collection."""
    # Create collection first
    client.post("/api/collections", json={"collection_name": "test-delete"})
    
    # Delete it
    response = client.delete("/api/collections/test-delete")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_delete_nonexistent_collection():
    """Test deleting non-existent collection fails."""
    response = client.delete("/api/collections/nonexistent")
    assert response.status_code == 404

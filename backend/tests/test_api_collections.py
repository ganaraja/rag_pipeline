"""
Integration tests for collection management API endpoints.

Tests the FastAPI endpoints for listing, creating, and deleting collections.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app, qdrant_manager


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_collections():
    """Clean up test collections before and after each test."""
    # Clean up before test
    collections = qdrant_manager.list_collections()
    for collection in collections:
        if collection.startswith("test_"):
            try:
                qdrant_manager.delete_collection(collection)
            except:
                pass
    
    yield
    
    # Clean up after test
    collections = qdrant_manager.list_collections()
    for collection in collections:
        if collection.startswith("test_"):
            try:
                qdrant_manager.delete_collection(collection)
            except:
                pass


class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestListCollections:
    """Tests for GET /api/collections endpoint."""
    
    def test_list_collections_empty(self, client):
        """Test listing collections when none exist."""
        response = client.get("/api/collections")
        assert response.status_code == 200
        collections = response.json()
        assert isinstance(collections, list)
    
    def test_list_collections_with_data(self, client):
        """Test listing collections when some exist."""
        # Create a test collection
        qdrant_manager.create_collection("test_collection_1")
        
        response = client.get("/api/collections")
        assert response.status_code == 200
        collections = response.json()
        assert isinstance(collections, list)
        assert "test_collection_1" in collections


class TestCreateCollection:
    """Tests for POST /api/collections endpoint."""
    
    def test_create_collection_success(self, client):
        """Test successful collection creation."""
        response = client.post(
            "/api/collections",
            json={"collection_name": "test_new_collection"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["collection_name"] == "test_new_collection"
        assert "message" in data
        
        # Verify collection was created
        collections = qdrant_manager.list_collections()
        assert "test_new_collection" in collections
    
    def test_create_collection_empty_name(self, client):
        """Test creating collection with empty name returns 422 (Pydantic validation)."""
        response = client.post(
            "/api/collections",
            json={"collection_name": ""}
        )
        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        assert "detail" in data
    
    def test_create_collection_whitespace_name(self, client):
        """Test creating collection with whitespace-only name returns 400."""
        response = client.post(
            "/api/collections",
            json={"collection_name": "   "}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_create_collection_duplicate(self, client):
        """Test creating duplicate collection returns 409."""
        # Create first collection
        qdrant_manager.create_collection("test_duplicate")
        
        # Try to create duplicate
        response = client.post(
            "/api/collections",
            json={"collection_name": "test_duplicate"}
        )
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()
    
    def test_create_collection_invalid_json(self, client):
        """Test creating collection with invalid JSON returns 422."""
        response = client.post(
            "/api/collections",
            json={"wrong_field": "test_collection"}
        )
        assert response.status_code == 422


class TestDeleteCollection:
    """Tests for DELETE /api/collections/{name} endpoint."""
    
    def test_delete_collection_success(self, client):
        """Test successful collection deletion."""
        # Create a collection first
        qdrant_manager.create_collection("test_to_delete")
        
        # Delete it
        response = client.delete("/api/collections/test_to_delete")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        
        # Verify collection was deleted
        collections = qdrant_manager.list_collections()
        assert "test_to_delete" not in collections
    
    def test_delete_collection_not_found(self, client):
        """Test deleting non-existent collection returns 404."""
        response = client.delete("/api/collections/nonexistent_collection")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "does not exist" in data["detail"].lower()
    
    def test_delete_collection_empty_name(self, client):
        """Test deleting collection with empty name returns 404."""
        response = client.delete("/api/collections/")
        # FastAPI returns 404 for missing path parameter
        assert response.status_code in [404, 405]


class TestCollectionWorkflow:
    """Integration tests for complete collection management workflows."""
    
    def test_create_list_delete_workflow(self, client):
        """Test complete workflow: create, list, delete."""
        # Create collection
        create_response = client.post(
            "/api/collections",
            json={"collection_name": "test_workflow"}
        )
        assert create_response.status_code == 200
        
        # List collections
        list_response = client.get("/api/collections")
        assert list_response.status_code == 200
        collections = list_response.json()
        assert "test_workflow" in collections
        
        # Delete collection
        delete_response = client.delete("/api/collections/test_workflow")
        assert delete_response.status_code == 200
        
        # Verify deletion
        list_response = client.get("/api/collections")
        collections = list_response.json()
        assert "test_workflow" not in collections
    
    def test_concurrent_collection_operations(self, client):
        """Test multiple collection operations in sequence."""
        # Create multiple collections
        for i in range(3):
            response = client.post(
                "/api/collections",
                json={"collection_name": f"test_concurrent_{i}"}
            )
            assert response.status_code == 200
        
        # List all collections
        response = client.get("/api/collections")
        collections = response.json()
        assert "test_concurrent_0" in collections
        assert "test_concurrent_1" in collections
        assert "test_concurrent_2" in collections
        
        # Delete all test collections
        for i in range(3):
            response = client.delete(f"/api/collections/test_concurrent_{i}")
            assert response.status_code == 200
    
    def test_create_after_delete(self, client):
        """Test creating a collection with the same name after deletion."""
        collection_name = "test_recreate"
        
        # Create collection
        response = client.post(
            "/api/collections",
            json={"collection_name": collection_name}
        )
        assert response.status_code == 200
        
        # Delete collection
        response = client.delete(f"/api/collections/{collection_name}")
        assert response.status_code == 200
        
        # Create again with same name
        response = client.post(
            "/api/collections",
            json={"collection_name": collection_name}
        )
        assert response.status_code == 200
        
        # Verify it exists
        response = client.get("/api/collections")
        collections = response.json()
        assert collection_name in collections


class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_special_characters_in_collection_name(self, client):
        """Test collection names with special characters."""
        # Qdrant allows alphanumeric, hyphens, and underscores
        valid_names = ["test-collection", "test_collection", "test123"]
        
        for name in valid_names:
            response = client.post(
                "/api/collections",
                json={"collection_name": name}
            )
            # Should succeed or fail gracefully
            assert response.status_code in [200, 400, 409]
    
    def test_very_long_collection_name(self, client):
        """Test collection name exceeding max length."""
        long_name = "test_" + "a" * 300  # Exceeds 255 char limit
        response = client.post(
            "/api/collections",
            json={"collection_name": long_name}
        )
        assert response.status_code == 422  # Pydantic validation error

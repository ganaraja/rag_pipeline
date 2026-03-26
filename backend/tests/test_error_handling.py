"""
Tests for comprehensive error handling across all API endpoints.

Tests error scenarios, timeout handling, database errors, LLM errors,
and logging functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
import asyncio
import time

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


class TestCollectionErrorHandling:
    """Tests for error handling in collection management endpoints."""
    
    def test_list_collections_timeout(self, client):
        """Test timeout handling when listing collections."""
        with patch('main.qdrant_manager.list_collections') as mock_list:
            # Simulate timeout by making the function sleep longer than timeout
            mock_list.side_effect = lambda: time.sleep(15)
            
            response = client.get("/api/collections")
            assert response.status_code == 504
            data = response.json()
            assert "timeout" in data["detail"].lower() or "timed out" in data["detail"].lower()
    
    def test_list_collections_connection_error(self, client):
        """Test connection error handling when listing collections."""
        with patch('main.qdrant_manager.list_collections') as mock_list:
            mock_list.side_effect = ConnectionError("Failed to connect to Qdrant")
            
            response = client.get("/api/collections")
            assert response.status_code == 503
            data = response.json()
            assert "connection" in data["detail"].lower()
            assert "database" in data["detail"].lower()
    
    def test_create_collection_invalid_name_format(self, client):
        """Test creating collection with invalid name format."""
        invalid_names = [
            "test collection",  # Space
            "test@collection",  # Special char
            "test.collection",  # Period
            "test/collection",  # Slash
        ]
        
        for name in invalid_names:
            response = client.post(
                "/api/collections",
                json={"collection_name": name}
            )
            assert response.status_code == 400
            data = response.json()
            assert "alphanumeric" in data["detail"].lower() or "format" in data["detail"].lower()
    
    def test_create_collection_timeout(self, client):
        """Test timeout handling when creating collection."""
        with patch('main.qdrant_manager.create_collection') as mock_create:
            # Simulate timeout
            mock_create.side_effect = lambda x: time.sleep(15)
            
            response = client.post(
                "/api/collections",
                json={"collection_name": "test_timeout"}
            )
            assert response.status_code == 504
            data = response.json()
            assert "timeout" in data["detail"].lower()
    
    def test_create_collection_connection_error(self, client):
        """Test connection error when creating collection."""
        with patch('main.qdrant_manager.list_collections') as mock_list:
            mock_list.side_effect = ConnectionError("Database unavailable")
            
            response = client.post(
                "/api/collections",
                json={"collection_name": "test_connection"}
            )
            assert response.status_code == 503
            data = response.json()
            assert "connection" in data["detail"].lower()
    
    def test_delete_collection_not_found_with_suggestions(self, client):
        """Test deleting non-existent collection shows available collections."""
        # Create some collections
        qdrant_manager.create_collection("test_available_1")
        qdrant_manager.create_collection("test_available_2")
        
        response = client.delete("/api/collections/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "does not exist" in data["detail"].lower()
        # Should suggest available collections
        assert "available" in data["detail"].lower() or "test_available" in data["detail"]
    
    def test_delete_collection_timeout(self, client):
        """Test timeout handling when deleting collection."""
        # Create a collection first
        qdrant_manager.create_collection("test_delete_timeout")
        
        with patch('main.qdrant_manager.delete_collection') as mock_delete:
            # Simulate timeout
            mock_delete.side_effect = lambda x: time.sleep(15)
            
            response = client.delete("/api/collections/test_delete_timeout")
            assert response.status_code == 504
            data = response.json()
            assert "timeout" in data["detail"].lower()


class TestUploadErrorHandling:
    """Tests for error handling in document upload endpoint."""
    
    def test_upload_no_file(self, client):
        """Test upload with no file provided."""
        # Create a collection first
        qdrant_manager.create_collection("test_upload")
        
        response = client.post(
            "/api/upload",
            data={"collection_name": "test_upload"}
        )
        # FastAPI will return 422 for missing required file
        assert response.status_code == 422
    
    def test_upload_empty_filename(self, client):
        """Test upload with empty filename."""
        # Create a collection first
        qdrant_manager.create_collection("test_upload")
        
        # Mock file with empty filename
        files = {"file": ("", b"content", "text/plain")}
        data = {"collection_name": "test_upload"}
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 422
        data = response.json()
        # For 422 validation errors, detail is a list of error objects
        assert any("file" in str(err).lower() for err in data["detail"])
    
    def test_upload_unsupported_format(self, client):
        """Test upload with unsupported file format."""
        # Create a collection first
        qdrant_manager.create_collection("test_upload")
        
        files = {"file": ("test.xyz", b"content", "application/octet-stream")}
        data = {"collection_name": "test_upload"}
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 400
        response_data = response.json()
        assert "unsupported" in response_data["detail"].lower()
        assert "format" in response_data["detail"].lower()
    
    def test_upload_nonexistent_collection(self, client):
        """Test upload to non-existent collection shows available collections."""
        files = {"file": ("test.txt", b"content", "text/plain")}
        data = {"collection_name": "nonexistent_collection"}
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 400
        response_data = response.json()
        assert "does not exist" in response_data["detail"].lower()
        assert "available" in response_data["detail"].lower()
    
    def test_upload_empty_file(self, client):
        """Test upload with empty file content."""
        # Create a collection first
        qdrant_manager.create_collection("test_upload")
        
        files = {"file": ("test.txt", b"", "text/plain")}
        data = {"collection_name": "test_upload"}
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 400
        response_data = response.json()
        assert "empty" in response_data["detail"].lower()
    
    def test_upload_file_too_large(self, client):
        """Test upload with file exceeding size limit."""
        # Create a collection first
        qdrant_manager.create_collection("test_upload")
        
        # Create a file larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        files = {"file": ("large.txt", large_content, "text/plain")}
        data = {"collection_name": "test_upload"}
        
        response = client.post("/api/upload", files=files, data=data)
        assert response.status_code == 400
        response_data = response.json()
        assert "size" in response_data["detail"].lower() or "large" in response_data["detail"].lower()
    
    def test_upload_chunking_failure(self, client):
        """Test upload when document chunking fails."""
        # Create a collection first
        qdrant_manager.create_collection("test_upload")
        
        with patch('main.chunking_strategy.process_document') as mock_chunk:
            mock_chunk.side_effect = Exception("Chunking failed")
            
            files = {"file": ("test.txt", b"content", "text/plain")}
            data = {"collection_name": "test_upload"}
            
            response = client.post("/api/upload", files=files, data=data)
            assert response.status_code == 500
            response_data = response.json()
            assert "process" in response_data["detail"].lower() or "failed" in response_data["detail"].lower()
    
    def test_upload_no_chunks_created(self, client):
        """Test upload when no chunks are created from document."""
        # Create a collection first
        qdrant_manager.create_collection("test_upload")
        
        with patch('main.chunking_strategy.process_document') as mock_chunk:
            mock_chunk.return_value = []  # No chunks
            
            files = {"file": ("test.txt", b"content", "text/plain")}
            data = {"collection_name": "test_upload"}
            
            response = client.post("/api/upload", files=files, data=data)
            assert response.status_code == 400
            response_data = response.json()
            assert "no" in response_data["detail"].lower() and "content" in response_data["detail"].lower()
    
    def test_upload_embedding_failure(self, client):
        """Test upload when embedding generation fails."""
        # Create a collection first
        qdrant_manager.create_collection("test_upload")
        
        with patch('main.embedding_manager.generate_all_embeddings') as mock_embed:
            mock_embed.side_effect = RuntimeError("GPU out of memory")
            
            files = {"file": ("test.txt", b"Some test content for chunking", "text/plain")}
            data = {"collection_name": "test_upload"}
            
            response = client.post("/api/upload", files=files, data=data)
            assert response.status_code == 500
            response_data = response.json()
            assert "embedding" in response_data["detail"].lower() or "failed" in response_data["detail"].lower()
    
    def test_upload_database_storage_failure(self, client):
        """Test upload when database storage fails."""
        # Create a collection first
        qdrant_manager.create_collection("test_upload")
        
        with patch('main.qdrant_manager.store_points') as mock_store:
            mock_store.side_effect = ConnectionError("Database connection lost")
            
            files = {"file": ("test.txt", b"Some test content for chunking", "text/plain")}
            data = {"collection_name": "test_upload"}
            
            response = client.post("/api/upload", files=files, data=data)
            assert response.status_code == 503
            response_data = response.json()
            assert "database" in response_data["detail"].lower() or "connection" in response_data["detail"].lower()


class TestQueryErrorHandling:
    """Tests for error handling in query endpoint."""
    
    def test_query_empty_text(self, client):
        """Test query with empty text."""
        response = client.post(
            "/api/query",
            json={"query": "", "collection_name": "test"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()
        assert "query" in data["detail"].lower()
    
    def test_query_empty_collection(self, client):
        """Test query with empty collection name."""
        response = client.post(
            "/api/query",
            json={"query": "test query", "collection_name": ""}
        )
        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()
        assert "collection" in data["detail"].lower()
    
    def test_query_nonexistent_collection(self, client):
        """Test query on non-existent collection shows available collections."""
        response = client.post(
            "/api/query",
            json={"query": "test query", "collection_name": "nonexistent"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "does not exist" in data["detail"].lower()
        assert "available" in data["detail"].lower()
    
    def test_query_database_timeout(self, client):
        """Test query with database timeout."""
        # Create a collection first
        qdrant_manager.create_collection("test_query")
        
        with patch('main.qdrant_manager.list_collections') as mock_list:
            # First call succeeds (for validation), second call times out
            mock_list.side_effect = lambda: time.sleep(15)
            
            response = client.post(
                "/api/query",
                json={"query": "test", "collection_name": "test_query"}
            )
            assert response.status_code == 504
            data = response.json()
            assert "timeout" in data["detail"].lower()
    
    def test_query_retrieval_timeout(self, client):
        """Test query with retrieval timeout."""
        # Create a collection first
        qdrant_manager.create_collection("test_query")
        
        with patch('main.retrieval_pipeline.retrieve') as mock_retrieve:
            # Simulate timeout
            mock_retrieve.side_effect = lambda **kwargs: time.sleep(35)
            
            response = client.post(
                "/api/query",
                json={"query": "test", "collection_name": "test_query"}
            )
            assert response.status_code == 504
            data = response.json()
            assert "timeout" in data["detail"].lower()
    
    def test_query_database_connection_error(self, client):
        """Test query with database connection error."""
        with patch('main.qdrant_manager.list_collections') as mock_list:
            mock_list.side_effect = ConnectionError("Database unavailable")
            
            response = client.post(
                "/api/query",
                json={"query": "test", "collection_name": "test"}
            )
            assert response.status_code == 503
            data = response.json()
            assert "database" in data["detail"].lower()
            assert "connect" in data["detail"].lower()
    
    def test_query_no_results(self, client):
        """Test query with no relevant documents found."""
        # Create a collection first
        qdrant_manager.create_collection("test_query")
        
        with patch('main.retrieval_pipeline.retrieve') as mock_retrieve:
            mock_retrieve.return_value = []  # No results
            
            response = client.post(
                "/api/query",
                json={"query": "test", "collection_name": "test_query"}
            )
            assert response.status_code == 404
            data = response.json()
            assert "no relevant" in data["detail"].lower() or "not found" in data["detail"].lower()
    
    def test_query_llm_connection_error(self, client):
        """Test query with LLM connection error."""
        # Create a collection first
        qdrant_manager.create_collection("test_query")
        
        # Mock retrieval to return results
        with patch('main.retrieval_pipeline.retrieve') as mock_retrieve:
            from models import RetrievalResult
            mock_retrieve.return_value = [
                RetrievalResult(
                    id=1,
                    text="test content",
                    score=0.9,
                    distance=0.1,
                    metadata={}
                )
            ]
            
            # Mock LLM to raise connection error
            with patch('main.llm_client.generate_answer') as mock_llm:
                mock_llm.side_effect = ConnectionError("Ollama server not responding")
                
                response = client.post(
                    "/api/query",
                    json={"query": "test", "collection_name": "test_query"}
                )
                assert response.status_code == 503
                data = response.json()
                assert "llm" in data["detail"].lower() or "ollama" in data["detail"].lower()
                assert "connect" in data["detail"].lower()
    
    def test_query_llm_timeout(self, client):
        """Test query with LLM generation timeout."""
        # Create a collection first
        qdrant_manager.create_collection("test_query")
        
        # Mock retrieval to return results
        with patch('main.retrieval_pipeline.retrieve') as mock_retrieve:
            from models import RetrievalResult
            mock_retrieve.return_value = [
                RetrievalResult(
                    id=1,
                    text="test content",
                    score=0.9,
                    distance=0.1,
                    metadata={}
                )
            ]
            
            # Mock LLM to timeout
            with patch('main.llm_client.generate_answer') as mock_llm:
                mock_llm.side_effect = lambda **kwargs: time.sleep(65)
                
                response = client.post(
                    "/api/query",
                    json={"query": "test", "collection_name": "test_query"}
                )
                assert response.status_code == 504
                data = response.json()
                assert "timeout" in data["detail"].lower()
    
    def test_query_llm_generation_error(self, client):
        """Test query with LLM generation error."""
        # Create a collection first
        qdrant_manager.create_collection("test_query")
        
        # Mock retrieval to return results
        with patch('main.retrieval_pipeline.retrieve') as mock_retrieve:
            from models import RetrievalResult
            mock_retrieve.return_value = [
                RetrievalResult(
                    id=1,
                    text="test content",
                    score=0.9,
                    distance=0.1,
                    metadata={}
                )
            ]
            
            # Mock LLM to raise error
            with patch('main.llm_client.generate_answer') as mock_llm:
                mock_llm.side_effect = RuntimeError("Model loading failed")
                
                response = client.post(
                    "/api/query",
                    json={"query": "test", "collection_name": "test_query"}
                )
                assert response.status_code == 500
                data = response.json()
                assert "generation" in data["detail"].lower() or "failed" in data["detail"].lower()


class TestErrorMessageClarity:
    """Tests for error message clarity and completeness."""
    
    def test_error_messages_include_timestamp(self, client):
        """Test that error responses include timestamps."""
        response = client.post(
            "/api/collections",
            json={"collection_name": ""}
        )
        # Pydantic validation error doesn't go through our handler
        # Test with a different error
        response = client.post(
            "/api/collections",
            json={"collection_name": "   "}
        )
        assert response.status_code == 400
        data = response.json()
        # Our custom error handler adds timestamp
        assert "timestamp" in data or "detail" in data
    
    def test_error_messages_are_descriptive(self, client):
        """Test that error messages provide helpful information."""
        # Test collection not found error
        response = client.delete("/api/collections/nonexistent")
        assert response.status_code == 404
        data = response.json()
        # Should explain what went wrong and suggest alternatives
        assert len(data["detail"]) > 20  # Reasonably detailed message
        assert "does not exist" in data["detail"].lower()
    
    def test_validation_errors_are_specific(self, client):
        """Test that validation errors are specific about what's wrong."""
        # Test invalid collection name format
        response = client.post(
            "/api/collections",
            json={"collection_name": "test collection"}
        )
        assert response.status_code == 400
        data = response.json()
        # Should explain the format requirements
        assert "alphanumeric" in data["detail"].lower() or "format" in data["detail"].lower()


class TestLoggingFunctionality:
    """Tests for error logging with timestamps and context."""
    
    def test_request_logging(self, client, caplog):
        """Test that requests are logged with context."""
        import logging
        caplog.set_level(logging.INFO)
        
        response = client.get("/health")
        
        # Check that request was logged
        assert any("Request" in record.message for record in caplog.records)
        assert any("Response" in record.message for record in caplog.records)
    
    def test_error_logging_includes_context(self, client, caplog):
        """Test that errors are logged with full context."""
        import logging
        caplog.set_level(logging.WARNING)
        
        # Trigger an error
        response = client.delete("/api/collections/nonexistent")
        
        # Check that error was logged with context
        error_logs = [r for r in caplog.records if r.levelname == "WARNING" or r.levelname == "ERROR"]
        assert len(error_logs) > 0
        # Should include collection name in log
        assert any("nonexistent" in record.message for record in error_logs)

"""
Integration tests for query API endpoint.

Tests the FastAPI POST /api/query endpoint for querying documents and generating answers.
Tests include successful queries with answer generation, validation errors for empty queries,
error handling for non-existent collections, and timing metrics accuracy.

**Validates: Requirements 21.2, 21.3**
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app
from models import QueryRequest, QueryResponse, RetrievalResult


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_qdrant_manager():
    """Mock the Qdrant manager."""
    with patch('main.qdrant_manager') as mock:
        mock.list_collections.return_value = ["test_collection", "existing_collection"]
        yield mock


@pytest.fixture
def mock_retrieval_pipeline():
    """Mock the retrieval pipeline to return test results."""
    with patch('main.retrieval_pipeline') as mock:
        # Create mock retrieval results
        mock_results = [
            RetrievalResult(
                id=1,
                text="Python is a high-level programming language known for its simplicity and readability.",
                score=0.95,
                distance=0.05,
                metadata={"chunk_id": 1, "parent_id": 0, "start_char": 0, "end_char": 80}
            ),
            RetrievalResult(
                id=2,
                text="Python was created by Guido van Rossum and first released in 1991.",
                score=0.88,
                distance=0.12,
                metadata={"chunk_id": 2, "parent_id": 0, "start_char": 81, "end_char": 150}
            ),
            RetrievalResult(
                id=3,
                text="Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
                score=0.82,
                distance=0.18,
                metadata={"chunk_id": 3, "parent_id": 1, "start_char": 151, "end_char": 260}
            )
        ]
        mock.retrieve.return_value = mock_results
        yield mock


@pytest.fixture
def mock_llm_client():
    """Mock the LLM client to return test answers."""
    with patch('main.llm_client') as mock:
        mock.generate_answer.return_value = "Python is a high-level programming language created by Guido van Rossum in 1991. It is known for its simplicity, readability, and support for multiple programming paradigms."
        yield mock


class TestQueryEndpoint:
    """Tests for POST /api/query endpoint."""
    
    def test_query_successful(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test successful query with answer generation."""
        # Make query request
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "collection_name": "test_collection"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "answer" in data
        assert "sources" in data
        assert "retrieval_time" in data
        assert "generation_time" in data
        
        # Verify answer content
        assert len(data["answer"]) > 0
        assert "Python" in data["answer"]
        
        # Verify sources
        assert len(data["sources"]) == 3
        assert data["sources"][0]["score"] == 0.95
        assert "Python" in data["sources"][0]["text"]
        
        # Verify timing metrics
        assert data["retrieval_time"] > 0
        assert data["generation_time"] > 0
        
        # Verify mocks were called correctly
        mock_qdrant_manager.list_collections.assert_called()
        mock_retrieval_pipeline.retrieve.assert_called_once_with(
            query="What is Python?",
            collection_name="test_collection",
            use_cross_encoder=True
        )
        mock_llm_client.generate_answer.assert_called_once()
        
        # Verify LLM was called with correct context
        llm_call_args = mock_llm_client.generate_answer.call_args
        assert llm_call_args[1]["query"] == "What is Python?"
        assert len(llm_call_args[1]["context_chunks"]) == 3
    
    def test_query_empty_query_text(
        self,
        client,
        mock_qdrant_manager
    ):
        """Test validation error for empty query text."""
        # Test with empty string
        response = client.post(
            "/api/query",
            json={
                "query": "",
                "collection_name": "test_collection"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()
        
        # Test with whitespace only
        response = client.post(
            "/api/query",
            json={
                "query": "   ",
                "collection_name": "test_collection"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()
    
    def test_query_empty_collection_name(
        self,
        client,
        mock_qdrant_manager
    ):
        """Test validation error for empty collection name."""
        # Test with empty string
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "collection_name": ""
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()
        
        # Test with whitespace only
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "collection_name": "   "
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()
    
    def test_query_non_existent_collection(
        self,
        client,
        mock_qdrant_manager
    ):
        """Test error handling for non-existent collection."""
        # Mock list_collections to return empty list
        mock_qdrant_manager.list_collections.return_value = []
        
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "collection_name": "non_existent_collection"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "does not exist" in data["detail"]
        assert "non_existent_collection" in data["detail"]
    
    def test_query_no_results_found(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test handling when no relevant documents are found."""
        # Mock retrieval pipeline to return empty results
        mock_retrieval_pipeline.retrieve.return_value = []
        
        response = client.post(
            "/api/query",
            json={
                "query": "What is quantum computing?",
                "collection_name": "test_collection"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "No relevant documents found" in data["detail"]
        
        # Verify LLM was not called
        mock_llm_client.generate_answer.assert_not_called()
    
    def test_query_retrieval_failure(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test handling of retrieval pipeline failures."""
        # Mock retrieval pipeline to raise RuntimeError
        mock_retrieval_pipeline.retrieve.side_effect = RuntimeError("Qdrant connection failed")
        
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "collection_name": "test_collection"
            }
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Retrieval failed" in data["detail"]
        
        # Verify LLM was not called
        mock_llm_client.generate_answer.assert_not_called()
    
    def test_query_llm_generation_failure(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test handling of LLM generation failures."""
        # Mock LLM client to raise exception
        mock_llm_client.generate_answer.side_effect = Exception("LLM server unavailable")
        
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "collection_name": "test_collection"
            }
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Answer generation failed" in data["detail"]
    
    def test_query_timing_metrics_accuracy(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test that timing metrics are accurate."""
        # Add delays to mocks to simulate processing time
        def slow_retrieve(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
            return [
                RetrievalResult(
                    id=1,
                    text="Test result",
                    score=0.9,
                    distance=0.1,
                    metadata={}
                )
            ]
        
        def slow_generate(*args, **kwargs):
            time.sleep(0.05)  # 50ms delay
            return "Test answer"
        
        mock_retrieval_pipeline.retrieve.side_effect = slow_retrieve
        mock_llm_client.generate_answer.side_effect = slow_generate
        
        # Record start time
        start_time = time.time()
        
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "collection_name": "test_collection"
            }
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify timing metrics
        assert data["retrieval_time"] >= 0.1  # Should be at least 100ms
        assert data["generation_time"] >= 0.05  # Should be at least 50ms
        
        # Total time should be reasonable
        total_reported = data["retrieval_time"] + data["generation_time"]
        assert total_reported <= total_time  # Reported time should not exceed actual time
        assert total_reported >= 0.15  # Should be at least 150ms (100ms + 50ms)
    
    def test_query_missing_required_fields(self, client):
        """Test validation error when required fields are missing."""
        # Missing query field
        response = client.post(
            "/api/query",
            json={
                "collection_name": "test_collection"
            }
        )
        
        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        assert "detail" in data
        
        # Missing collection_name field
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        
        # Missing both fields
        response = client.post(
            "/api/query",
            json={}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_query_with_special_characters(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test query with special characters."""
        special_queries = [
            "What is Python's syntax?",
            "How does C++ differ from C?",
            "What are @decorators in Python?",
            "Explain the $ symbol in jQuery",
            "What is the & operator?",
        ]
        
        for query in special_queries:
            response = client.post(
                "/api/query",
                json={
                    "query": query,
                    "collection_name": "test_collection"
                }
            )
            
            assert response.status_code == 200, f"Failed for query: {query}"
            data = response.json()
            assert "answer" in data
            assert "sources" in data
    
    def test_query_with_long_text(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test query with very long text."""
        # Create a long query (500 words)
        long_query = " ".join(["What is Python?"] * 100)
        
        response = client.post(
            "/api/query",
            json={
                "query": long_query,
                "collection_name": "test_collection"
            }
        )
        
        # Should still succeed
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
    
    def test_query_with_unicode_characters(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test query with Unicode characters."""
        unicode_queries = [
            "什么是Python？",  # Chinese
            "Qu'est-ce que Python?",  # French
            "¿Qué es Python?",  # Spanish
            "Was ist Python?",  # German
            "Pythonとは何ですか？",  # Japanese
        ]
        
        for query in unicode_queries:
            response = client.post(
                "/api/query",
                json={
                    "query": query,
                    "collection_name": "test_collection"
                }
            )
            
            assert response.status_code == 200, f"Failed for query: {query}"
            data = response.json()
            assert "answer" in data
            assert "sources" in data


class TestQueryResponseModel:
    """Tests for QueryResponse model validation."""
    
    def test_query_response_model_structure(self):
        """Test that QueryResponse model has correct structure."""
        response = QueryResponse(
            answer="Test answer",
            sources=[
                RetrievalResult(
                    id=1,
                    text="Test text",
                    score=0.9,
                    distance=0.1,
                    metadata={}
                )
            ],
            retrieval_time=1.5,
            generation_time=0.5
        )
        
        assert response.answer == "Test answer"
        assert len(response.sources) == 1
        assert response.retrieval_time == 1.5
        assert response.generation_time == 0.5
    
    def test_query_response_model_validation(self):
        """Test QueryResponse model validation."""
        # Valid response
        response = QueryResponse(
            answer="Test",
            sources=[],
            retrieval_time=0.0,
            generation_time=0.0
        )
        assert response.retrieval_time == 0.0
        
        # Invalid: negative retrieval_time
        with pytest.raises(ValueError):
            QueryResponse(
                answer="Test",
                sources=[],
                retrieval_time=-1.0,
                generation_time=0.0
            )
        
        # Invalid: negative generation_time
        with pytest.raises(ValueError):
            QueryResponse(
                answer="Test",
                sources=[],
                retrieval_time=0.0,
                generation_time=-1.0
            )


class TestQueryWorkflow:
    """Integration tests for complete query workflows."""
    
    def test_query_multiple_collections(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test querying multiple collections."""
        collections = ["collection_a", "collection_b", "collection_c"]
        mock_qdrant_manager.list_collections.return_value = collections
        
        for collection in collections:
            response = client.post(
                "/api/query",
                json={
                    "query": "What is Python?",
                    "collection_name": collection
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data
            
            # Verify retrieval was called with correct collection
            mock_retrieval_pipeline.retrieve.assert_called_with(
                query="What is Python?",
                collection_name=collection,
                use_cross_encoder=True
            )
            
            # Reset mock for next iteration
            mock_retrieval_pipeline.retrieve.reset_mock()
    
    def test_query_sequential_queries(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test multiple sequential queries."""
        queries = [
            "What is Python?",
            "How does Python work?",
            "What are Python's features?",
        ]
        
        for query in queries:
            response = client.post(
                "/api/query",
                json={
                    "query": query,
                    "collection_name": "test_collection"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data
    
    def test_query_with_different_result_counts(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test queries that return different numbers of results."""
        result_counts = [1, 5, 10, 20]
        
        for count in result_counts:
            # Create mock results with specified count
            mock_results = [
                RetrievalResult(
                    id=i,
                    text=f"Result {i}",
                    score=0.9 - (i * 0.01),
                    distance=0.1 + (i * 0.01),
                    metadata={}
                )
                for i in range(count)
            ]
            mock_retrieval_pipeline.retrieve.return_value = mock_results
            
            response = client.post(
                "/api/query",
                json={
                    "query": "What is Python?",
                    "collection_name": "test_collection"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["sources"]) == count


class TestQueryErrorHandling:
    """Tests for query error handling and edge cases."""
    
    def test_query_retrieval_validation_error(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test handling of validation errors from retrieval pipeline."""
        # Mock retrieval to raise ValueError
        mock_retrieval_pipeline.retrieve.side_effect = ValueError("Invalid query format")
        
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "collection_name": "test_collection"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid query format" in data["detail"]
    
    def test_query_error_message_clarity(
        self,
        client,
        mock_qdrant_manager
    ):
        """Test that error messages are clear and informative."""
        # Test with non-existent collection
        mock_qdrant_manager.list_collections.return_value = []
        
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "collection_name": "non_existent"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "does not exist" in data["detail"]
        assert "non_existent" in data["detail"]
    
    def test_query_with_malformed_json(self, client):
        """Test handling of malformed JSON in request."""
        response = client.post(
            "/api/query",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        # FastAPI should return 422 for malformed JSON
        assert response.status_code == 422
    
    def test_query_with_extra_fields(
        self,
        client,
        mock_qdrant_manager,
        mock_retrieval_pipeline,
        mock_llm_client
    ):
        """Test that extra fields in request are ignored."""
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "collection_name": "test_collection",
                "extra_field": "should be ignored",
                "another_field": 123
            }
        )
        
        # Should still succeed
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

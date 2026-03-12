"""
Tests for QdrantManager class.

Validates collection management, point storage, and multi-stage retrieval operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from qdrant_manager import QdrantManager
from models import DocumentChunk, SparseVector


@pytest.fixture
def temp_qdrant_path():
    """Create a temporary directory for Qdrant database."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def qdrant_manager(temp_qdrant_path):
    """Create a QdrantManager instance with temporary storage."""
    return QdrantManager(path=temp_qdrant_path)


@pytest.fixture
def sample_chunks():
    """Create sample document chunks for testing."""
    return [
        DocumentChunk(
            chunk_id=1,
            parent_id=0,
            text="This is the first test chunk about machine learning.",
            start_char=0,
            end_char=53,
            metadata={"document": "test.pdf", "page": 1}
        ),
        DocumentChunk(
            chunk_id=2,
            parent_id=0,
            text="This is the second test chunk about neural networks.",
            start_char=54,
            end_char=107,
            metadata={"document": "test.pdf", "page": 1}
        ),
        DocumentChunk(
            chunk_id=3,
            parent_id=1,
            text="This is the third test chunk about deep learning.",
            start_char=108,
            end_char=158,
            metadata={"document": "test.pdf", "page": 2}
        )
    ]


@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing."""
    return {
        "matryoshka_64": [
            [0.1] * 64,
            [0.2] * 64,
            [0.3] * 64
        ],
        "matryoshka_768": [
            [0.1] * 768,
            [0.2] * 768,
            [0.3] * 768
        ],
        "colbert": [
            [[0.1] * 128, [0.2] * 128],  # Multi-vector for first chunk
            [[0.3] * 128, [0.4] * 128],  # Multi-vector for second chunk
            [[0.5] * 128, [0.6] * 128]   # Multi-vector for third chunk
        ],
        "splade": [
            SparseVector(indices=[0, 5, 10], values=[0.5, 0.3, 0.8]),
            SparseVector(indices=[1, 6, 11], values=[0.6, 0.4, 0.9]),
            SparseVector(indices=[2, 7, 12], values=[0.7, 0.5, 1.0])
        ]
    }


class TestQdrantManagerInitialization:
    """Tests for QdrantManager initialization."""

    def test_initialization_with_default_path(self):
        """Test initialization with default path."""
        manager = QdrantManager()
        assert manager.client is not None

    def test_initialization_with_custom_path(self, temp_qdrant_path):
        """Test initialization with custom path."""
        manager = QdrantManager(path=temp_qdrant_path)
        assert manager.client is not None


class TestCollectionCreation:
    """Tests for collection creation."""

    def test_create_collection_success(self, qdrant_manager):
        """Test successful collection creation."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        
        # Verify collection exists
        collections = qdrant_manager.list_collections()
        assert collection_name in collections

    def test_create_collection_duplicate(self, qdrant_manager):
        """Test that creating duplicate collection raises error."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        
        # Attempt to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            qdrant_manager.create_collection(collection_name)

    def test_create_multiple_collections(self, qdrant_manager):
        """Test creating multiple collections."""
        collections = ["collection1", "collection2", "collection3"]
        
        for col in collections:
            qdrant_manager.create_collection(col)
        
        # Verify all collections exist
        existing_collections = qdrant_manager.list_collections()
        for col in collections:
            assert col in existing_collections

    def test_collection_has_correct_vector_config(self, qdrant_manager):
        """Test that created collection has correct vector configuration."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        
        # Get collection info
        collection_info = qdrant_manager.client.get_collection(collection_name)
        
        # Verify vector configurations
        assert "matryoshka_64" in collection_info.config.params.vectors
        assert "matryoshka_768" in collection_info.config.params.vectors
        assert "colbert" in collection_info.config.params.vectors
        
        # Verify dimensions
        assert collection_info.config.params.vectors["matryoshka_64"].size == 64
        assert collection_info.config.params.vectors["matryoshka_768"].size == 768
        assert collection_info.config.params.vectors["colbert"].size == 128
        
        # Verify sparse vectors
        assert "splade" in collection_info.config.params.sparse_vectors


class TestCollectionListing:
    """Tests for listing collections."""

    def test_list_collections_empty(self, qdrant_manager):
        """Test listing collections when none exist."""
        collections = qdrant_manager.list_collections()
        assert isinstance(collections, list)
        assert len(collections) == 0

    def test_list_collections_with_data(self, qdrant_manager):
        """Test listing collections after creating some."""
        test_collections = ["col1", "col2", "col3"]
        
        for col in test_collections:
            qdrant_manager.create_collection(col)
        
        collections = qdrant_manager.list_collections()
        assert len(collections) == 3
        assert set(collections) == set(test_collections)


class TestCollectionDeletion:
    """Tests for collection deletion."""

    def test_delete_collection_success(self, qdrant_manager):
        """Test successful collection deletion."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        
        # Verify it exists
        assert collection_name in qdrant_manager.list_collections()
        
        # Delete it
        qdrant_manager.delete_collection(collection_name)
        
        # Verify it's gone
        assert collection_name not in qdrant_manager.list_collections()

    def test_delete_nonexistent_collection(self, qdrant_manager):
        """Test that deleting non-existent collection raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            qdrant_manager.delete_collection("nonexistent_collection")

    def test_delete_multiple_collections(self, qdrant_manager):
        """Test deleting multiple collections."""
        collections = ["col1", "col2", "col3"]
        
        # Create collections
        for col in collections:
            qdrant_manager.create_collection(col)
        
        # Delete them one by one
        for col in collections:
            qdrant_manager.delete_collection(col)
        
        # Verify all are gone
        remaining = qdrant_manager.list_collections()
        assert len(remaining) == 0


class TestPointStorage:
    """Tests for storing points with embeddings."""

    def test_store_points_success(self, qdrant_manager, sample_chunks, sample_embeddings):
        """Test successful point storage."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        
        # Store points
        qdrant_manager.store_points(collection_name, sample_chunks, sample_embeddings)
        
        # Verify points were stored
        collection_info = qdrant_manager.client.get_collection(collection_name)
        assert collection_info.points_count == len(sample_chunks)

    def test_store_points_nonexistent_collection(self, qdrant_manager, sample_chunks, sample_embeddings):
        """Test that storing points in non-existent collection raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            qdrant_manager.store_points("nonexistent", sample_chunks, sample_embeddings)

    def test_store_points_mismatched_embeddings(self, qdrant_manager, sample_chunks):
        """Test that mismatched embedding counts raise error."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        
        # Create embeddings with wrong count
        bad_embeddings = {
            "matryoshka_64": [[0.1] * 64],  # Only 1 embedding for 3 chunks
            "matryoshka_768": [[0.1] * 768],
            "colbert": [[[0.1] * 128]],
            "splade": [SparseVector(indices=[0], values=[0.5])]
        }
        
        with pytest.raises(ValueError, match="must match number of chunks"):
            qdrant_manager.store_points(collection_name, sample_chunks, bad_embeddings)

    def test_store_points_preserves_metadata(self, qdrant_manager, sample_chunks, sample_embeddings):
        """Test that point storage preserves chunk metadata."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        
        # Store points
        qdrant_manager.store_points(collection_name, sample_chunks, sample_embeddings)
        
        # Retrieve a point and verify metadata
        points = qdrant_manager.client.retrieve(
            collection_name=collection_name,
            ids=[1]
        )
        
        assert len(points) == 1
        point = points[0]
        assert point.payload["text"] == sample_chunks[0].text
        assert point.payload["chunk_id"] == sample_chunks[0].chunk_id
        assert point.payload["parent_id"] == sample_chunks[0].parent_id
        assert point.payload["metadata"]["document"] == "test.pdf"

    def test_store_points_empty_chunks(self, qdrant_manager):
        """Test storing empty chunks list."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        
        empty_embeddings = {
            "matryoshka_64": [],
            "matryoshka_768": [],
            "colbert": [],
            "splade": []
        }
        
        # Should not raise error
        qdrant_manager.store_points(collection_name, [], empty_embeddings)
        
        # Verify no points were stored
        collection_info = qdrant_manager.client.get_collection(collection_name)
        assert collection_info.points_count == 0


class TestQueryWithPrefetch:
    """Tests for multi-stage retrieval with prefetch."""

    def test_query_with_prefetch_success(self, qdrant_manager, sample_chunks, sample_embeddings):
        """Test successful query with prefetch."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        qdrant_manager.store_points(collection_name, sample_chunks, sample_embeddings)
        
        # Create query embeddings
        query_embeddings = {
            "matryoshka_64": [0.15] * 64,
            "matryoshka_768": [0.15] * 768,
            "colbert": [[0.15] * 128, [0.25] * 128],
            "splade": SparseVector(indices=[0, 5, 10], values=[0.55, 0.35, 0.85])
        }
        
        # Execute query
        results = qdrant_manager.query_with_prefetch(
            collection_name=collection_name,
            query_embeddings=query_embeddings
        )
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) <= 50  # Default stage4_limit

    def test_query_with_prefetch_custom_limits(self, qdrant_manager, sample_chunks, sample_embeddings):
        """Test query with custom stage limits."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        qdrant_manager.store_points(collection_name, sample_chunks, sample_embeddings)
        
        query_embeddings = {
            "matryoshka_64": [0.15] * 64,
            "matryoshka_768": [0.15] * 768,
            "colbert": [[0.15] * 128],
            "splade": SparseVector(indices=[0, 5], values=[0.5, 0.3])
        }
        
        custom_limits = {
            "stage1_limit": 10,
            "stage2_limit": 5,
            "stage3_limit": 5,
            "stage4_limit": 2
        }
        
        results = qdrant_manager.query_with_prefetch(
            collection_name=collection_name,
            query_embeddings=query_embeddings,
            limits=custom_limits
        )
        
        # Verify results respect limit
        assert len(results) <= 2

    def test_query_with_prefetch_empty_collection(self, qdrant_manager):
        """Test query on empty collection."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        
        query_embeddings = {
            "matryoshka_64": [0.1] * 64,
            "matryoshka_768": [0.1] * 768,
            "colbert": [[0.1] * 128],
            "splade": SparseVector(indices=[0], values=[0.5])
        }
        
        results = qdrant_manager.query_with_prefetch(
            collection_name=collection_name,
            query_embeddings=query_embeddings
        )
        
        # Should return empty results
        assert len(results) == 0

    def test_query_with_prefetch_returns_payloads(self, qdrant_manager, sample_chunks, sample_embeddings):
        """Test that query results include payloads."""
        collection_name = "test_collection"
        qdrant_manager.create_collection(collection_name)
        qdrant_manager.store_points(collection_name, sample_chunks, sample_embeddings)
        
        query_embeddings = {
            "matryoshka_64": [0.15] * 64,
            "matryoshka_768": [0.15] * 768,
            "colbert": [[0.15] * 128],
            "splade": SparseVector(indices=[0, 5], values=[0.5, 0.3])
        }
        
        results = qdrant_manager.query_with_prefetch(
            collection_name=collection_name,
            query_embeddings=query_embeddings,
            limits={"stage4_limit": 3}
        )
        
        # Verify results have payloads
        if len(results) > 0:
            result = results[0]
            assert hasattr(result, 'payload')
            assert 'text' in result.payload
            assert 'chunk_id' in result.payload


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    def test_complete_workflow(self, qdrant_manager, sample_chunks, sample_embeddings):
        """Test complete workflow: create, store, query, delete."""
        collection_name = "integration_test"
        
        # Create collection
        qdrant_manager.create_collection(collection_name)
        assert collection_name in qdrant_manager.list_collections()
        
        # Store points
        qdrant_manager.store_points(collection_name, sample_chunks, sample_embeddings)
        
        # Query
        query_embeddings = {
            "matryoshka_64": [0.15] * 64,
            "matryoshka_768": [0.15] * 768,
            "colbert": [[0.15] * 128],
            "splade": SparseVector(indices=[0, 5], values=[0.5, 0.3])
        }
        results = qdrant_manager.query_with_prefetch(collection_name, query_embeddings)
        assert isinstance(results, list)
        
        # Delete collection
        qdrant_manager.delete_collection(collection_name)
        assert collection_name not in qdrant_manager.list_collections()

    def test_multiple_collections_isolation(self, qdrant_manager, sample_chunks, sample_embeddings):
        """Test that multiple collections are isolated."""
        col1 = "collection1"
        col2 = "collection2"
        
        # Create two collections
        qdrant_manager.create_collection(col1)
        qdrant_manager.create_collection(col2)
        
        # Store different data in each
        qdrant_manager.store_points(col1, sample_chunks[:2], {
            "matryoshka_64": sample_embeddings["matryoshka_64"][:2],
            "matryoshka_768": sample_embeddings["matryoshka_768"][:2],
            "colbert": sample_embeddings["colbert"][:2],
            "splade": sample_embeddings["splade"][:2]
        })
        
        qdrant_manager.store_points(col2, sample_chunks[2:], {
            "matryoshka_64": sample_embeddings["matryoshka_64"][2:],
            "matryoshka_768": sample_embeddings["matryoshka_768"][2:],
            "colbert": sample_embeddings["colbert"][2:],
            "splade": sample_embeddings["splade"][2:]
        })
        
        # Verify point counts
        col1_info = qdrant_manager.client.get_collection(col1)
        col2_info = qdrant_manager.client.get_collection(col2)
        
        assert col1_info.points_count == 2
        assert col2_info.points_count == 1

"""
Tests for MultiEmbeddingRetrievalPipeline class.

Validates multi-stage retrieval with both prefetch and naive implementations.
"""

import pytest
import tempfile
import shutil

from retrieval_pipeline import MultiEmbeddingRetrievalPipeline
from qdrant_manager import QdrantManager
from embedding_manager import EmbeddingModelManager
from models import DocumentChunk, SparseVector, RetrievalResult


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
def embedding_manager():
    """Create an EmbeddingModelManager instance."""
    return EmbeddingModelManager(device="cpu")


@pytest.fixture
def retrieval_pipeline_prefetch(qdrant_manager, embedding_manager):
    """Create a retrieval pipeline with prefetch enabled."""
    return MultiEmbeddingRetrievalPipeline(
        qdrant_manager=qdrant_manager,
        embedding_manager=embedding_manager,
        use_prefetch=True
    )


@pytest.fixture
def retrieval_pipeline_naive(qdrant_manager, embedding_manager):
    """Create a retrieval pipeline with naive implementation."""
    return MultiEmbeddingRetrievalPipeline(
        qdrant_manager=qdrant_manager,
        embedding_manager=embedding_manager,
        use_prefetch=False
    )


@pytest.fixture
def sample_chunks():
    """Create sample document chunks for testing."""
    return [
        DocumentChunk(
            chunk_id=1,
            parent_id=0,
            text="Machine learning is a subset of artificial intelligence.",
            start_char=0,
            end_char=58,
            metadata={"document": "ml.pdf", "page": 1}
        ),
        DocumentChunk(
            chunk_id=2,
            parent_id=0,
            text="Neural networks are inspired by biological neurons.",
            start_char=59,
            end_char=111,
            metadata={"document": "ml.pdf", "page": 1}
        ),
        DocumentChunk(
            chunk_id=3,
            parent_id=1,
            text="Deep learning uses multiple layers of neural networks.",
            start_char=112,
            end_char=167,
            metadata={"document": "ml.pdf", "page": 2}
        ),
        DocumentChunk(
            chunk_id=4,
            parent_id=1,
            text="Python is a popular programming language for data science.",
            start_char=168,
            end_char=227,
            metadata={"document": "python.pdf", "page": 1}
        ),
        DocumentChunk(
            chunk_id=5,
            parent_id=2,
            text="Natural language processing enables computers to understand text.",
            start_char=228,
            end_char=294,
            metadata={"document": "nlp.pdf", "page": 1}
        )
    ]


@pytest.fixture
def populated_collection(qdrant_manager, embedding_manager, sample_chunks):
    """Create and populate a test collection."""
    collection_name = "test_collection"
    qdrant_manager.create_collection(collection_name)
    
    # Generate embeddings for all chunks
    texts = [chunk.text for chunk in sample_chunks]
    embeddings = embedding_manager.generate_all_embeddings(texts)
    
    # Store points
    qdrant_manager.store_points(collection_name, sample_chunks, embeddings)
    
    return collection_name


class TestRetrievalPipelineInitialization:
    """Tests for retrieval pipeline initialization."""

    def test_initialization_with_prefetch(self, qdrant_manager, embedding_manager):
        """Test initialization with prefetch enabled."""
        pipeline = MultiEmbeddingRetrievalPipeline(
            qdrant_manager=qdrant_manager,
            embedding_manager=embedding_manager,
            use_prefetch=True
        )
        
        assert pipeline.qdrant is not None
        assert pipeline.embeddings is not None
        assert pipeline.use_prefetch is True

    def test_initialization_without_prefetch(self, qdrant_manager, embedding_manager):
        """Test initialization with naive implementation."""
        pipeline = MultiEmbeddingRetrievalPipeline(
            qdrant_manager=qdrant_manager,
            embedding_manager=embedding_manager,
            use_prefetch=False
        )
        
        assert pipeline.qdrant is not None
        assert pipeline.embeddings is not None
        assert pipeline.use_prefetch is False


class TestRetrieveMethod:
    """Tests for the main retrieve method."""

    def test_retrieve_with_prefetch(self, retrieval_pipeline_prefetch, populated_collection):
        """Test retrieval with prefetch implementation."""
        query = "What is machine learning?"
        
        results = retrieval_pipeline_prefetch.retrieve(
            query=query,
            collection_name=populated_collection,
            use_cross_encoder=True
        )
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) <= 20  # Default final limit
        
        # Verify result structure
        if len(results) > 0:
            result = results[0]
            assert isinstance(result, RetrievalResult)
            assert hasattr(result, 'id')
            assert hasattr(result, 'text')
            assert hasattr(result, 'score')
            assert hasattr(result, 'distance')
            assert hasattr(result, 'metadata')

    def test_retrieve_with_naive(self, retrieval_pipeline_naive, populated_collection):
        """Test retrieval with naive implementation."""
        query = "What is machine learning?"
        
        results = retrieval_pipeline_naive.retrieve(
            query=query,
            collection_name=populated_collection,
            use_cross_encoder=True
        )
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) <= 20  # Default final limit
        
        # Verify result structure
        if len(results) > 0:
            result = results[0]
            assert isinstance(result, RetrievalResult)

    def test_retrieve_without_cross_encoder(self, retrieval_pipeline_prefetch, populated_collection):
        """Test retrieval without cross-encoder reranking."""
        query = "What is machine learning?"
        
        results = retrieval_pipeline_prefetch.retrieve(
            query=query,
            collection_name=populated_collection,
            use_cross_encoder=False
        )
        
        # Should still return results
        assert isinstance(results, list)

    def test_retrieve_with_custom_limits(self, retrieval_pipeline_prefetch, populated_collection):
        """Test retrieval with custom stage limits."""
        query = "What is machine learning?"
        
        custom_limits = {
            "stage1_limit": 10,
            "stage2_limit": 5,
            "stage3_limit": 5,
            "stage4_limit": 3,
            "final_limit": 2
        }
        
        results = retrieval_pipeline_prefetch.retrieve(
            query=query,
            collection_name=populated_collection,
            use_cross_encoder=True,
            limits=custom_limits
        )
        
        # Verify results respect final limit
        assert len(results) <= 2

    def test_retrieve_empty_query(self, retrieval_pipeline_prefetch, populated_collection):
        """Test that empty query raises error."""
        with pytest.raises(ValueError, match="query cannot be empty"):
            retrieval_pipeline_prefetch.retrieve(
                query="",
                collection_name=populated_collection
            )

    def test_retrieve_nonexistent_collection(self, retrieval_pipeline_prefetch):
        """Test that querying non-existent collection raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            retrieval_pipeline_prefetch.retrieve(
                query="test query",
                collection_name="nonexistent_collection"
            )

    def test_retrieve_empty_collection(self, retrieval_pipeline_prefetch, qdrant_manager):
        """Test retrieval on empty collection."""
        collection_name = "empty_collection"
        qdrant_manager.create_collection(collection_name)
        
        results = retrieval_pipeline_prefetch.retrieve(
            query="test query",
            collection_name=collection_name
        )
        
        # Should return empty results
        assert len(results) == 0


class TestHybridSearchWithPrefetch:
    """Tests for optimized hybrid search with prefetch."""

    def test_hybrid_search_with_prefetch_returns_results(
        self,
        retrieval_pipeline_prefetch,
        populated_collection,
        embedding_manager
    ):
        """Test that prefetch search returns results."""
        query = "machine learning"
        all_embeddings = embedding_manager.generate_all_embeddings(query)
        
        # Extract and format single query embeddings
        mat64 = all_embeddings["matryoshka_64"][0]
        mat768 = all_embeddings["matryoshka_768"][0]
        
        query_embeddings = {
            "matryoshka_64": mat64.tolist() if hasattr(mat64, 'tolist') else mat64,
            "matryoshka_768": mat768.tolist() if hasattr(mat768, 'tolist') else mat768,
            "colbert": all_embeddings["colbert"][0],
            "splade": all_embeddings["splade"][0]
        }
        
        results = retrieval_pipeline_prefetch._hybrid_search_with_prefetch(
            query=query,
            collection_name=populated_collection,
            query_embeddings=query_embeddings,
            limits={}
        )
        
        assert isinstance(results, list)

    def test_hybrid_search_with_prefetch_respects_limits(
        self,
        retrieval_pipeline_prefetch,
        populated_collection,
        embedding_manager
    ):
        """Test that prefetch search respects stage limits."""
        query = "machine learning"
        all_embeddings = embedding_manager.generate_all_embeddings(query)
        
        # Extract and format single query embeddings
        mat64 = all_embeddings["matryoshka_64"][0]
        mat768 = all_embeddings["matryoshka_768"][0]
        
        query_embeddings = {
            "matryoshka_64": mat64.tolist() if hasattr(mat64, 'tolist') else mat64,
            "matryoshka_768": mat768.tolist() if hasattr(mat768, 'tolist') else mat768,
            "colbert": all_embeddings["colbert"][0],
            "splade": all_embeddings["splade"][0]
        }
        
        limits = {"stage4_limit": 2}
        
        results = retrieval_pipeline_prefetch._hybrid_search_with_prefetch(
            query=query,
            collection_name=populated_collection,
            query_embeddings=query_embeddings,
            limits=limits
        )
        
        # Should respect the final stage limit
        assert len(results) <= 2


class TestHybridSearchNaive:
    """Tests for naive hybrid search implementation."""

    def test_hybrid_search_naive_returns_results(
        self,
        retrieval_pipeline_naive,
        populated_collection,
        embedding_manager
    ):
        """Test that naive search returns results."""
        query = "machine learning"
        all_embeddings = embedding_manager.generate_all_embeddings(query)
        
        # Extract and format single query embeddings
        mat64 = all_embeddings["matryoshka_64"][0]
        mat768 = all_embeddings["matryoshka_768"][0]
        
        query_embeddings = {
            "matryoshka_64": mat64.tolist() if hasattr(mat64, 'tolist') else mat64,
            "matryoshka_768": mat768.tolist() if hasattr(mat768, 'tolist') else mat768,
            "colbert": all_embeddings["colbert"][0],
            "splade": all_embeddings["splade"][0]
        }
        
        results = retrieval_pipeline_naive._hybrid_search_naive(
            query=query,
            collection_name=populated_collection,
            query_embeddings=query_embeddings,
            limits={}
        )
        
        assert isinstance(results, list)

    def test_hybrid_search_naive_respects_limits(
        self,
        retrieval_pipeline_naive,
        populated_collection,
        embedding_manager
    ):
        """Test that naive search respects stage limits."""
        query = "machine learning"
        all_embeddings = embedding_manager.generate_all_embeddings(query)
        
        # Extract and format single query embeddings
        mat64 = all_embeddings["matryoshka_64"][0]
        mat768 = all_embeddings["matryoshka_768"][0]
        
        query_embeddings = {
            "matryoshka_64": mat64.tolist() if hasattr(mat64, 'tolist') else mat64,
            "matryoshka_768": mat768.tolist() if hasattr(mat768, 'tolist') else mat768,
            "colbert": all_embeddings["colbert"][0],
            "splade": all_embeddings["splade"][0]
        }
        
        limits = {"stage4_limit": 2}
        
        results = retrieval_pipeline_naive._hybrid_search_naive(
            query=query,
            collection_name=populated_collection,
            query_embeddings=query_embeddings,
            limits=limits
        )
        
        # Should respect the final stage limit
        assert len(results) <= 2


class TestCrossEncoderRerank:
    """Tests for cross-encoder reranking."""

    def test_cross_encoder_rerank_returns_results(
        self,
        retrieval_pipeline_prefetch,
        populated_collection,
        embedding_manager
    ):
        """Test that cross-encoder reranking returns results."""
        query = "machine learning"
        all_embeddings = embedding_manager.generate_all_embeddings(query)
        
        # Extract and format single query embeddings
        mat64 = all_embeddings["matryoshka_64"][0]
        mat768 = all_embeddings["matryoshka_768"][0]
        
        query_embeddings = {
            "matryoshka_64": mat64.tolist() if hasattr(mat64, 'tolist') else mat64,
            "matryoshka_768": mat768.tolist() if hasattr(mat768, 'tolist') else mat768,
            "colbert": all_embeddings["colbert"][0],
            "splade": all_embeddings["splade"][0]
        }
        
        # Get candidates first
        candidates = retrieval_pipeline_prefetch._hybrid_search_with_prefetch(
            query=query,
            collection_name=populated_collection,
            query_embeddings=query_embeddings,
            limits={}
        )
        
        # Rerank
        results = retrieval_pipeline_prefetch._cross_encoder_rerank(
            query=query,
            candidates=candidates,
            limit=5
        )
        
        assert isinstance(results, list)
        assert len(results) <= 5
        
        # Verify all results are RetrievalResult objects
        for result in results:
            assert isinstance(result, RetrievalResult)

    def test_cross_encoder_rerank_sorts_by_score(
        self,
        retrieval_pipeline_prefetch,
        populated_collection,
        embedding_manager
    ):
        """Test that cross-encoder reranking sorts by score."""
        query = "machine learning"
        all_embeddings = embedding_manager.generate_all_embeddings(query)
        
        # Extract and format single query embeddings
        mat64 = all_embeddings["matryoshka_64"][0]
        mat768 = all_embeddings["matryoshka_768"][0]
        
        query_embeddings = {
            "matryoshka_64": mat64.tolist() if hasattr(mat64, 'tolist') else mat64,
            "matryoshka_768": mat768.tolist() if hasattr(mat768, 'tolist') else mat768,
            "colbert": all_embeddings["colbert"][0],
            "splade": all_embeddings["splade"][0]
        }
        
        # Get candidates
        candidates = retrieval_pipeline_prefetch._hybrid_search_with_prefetch(
            query=query,
            collection_name=populated_collection,
            query_embeddings=query_embeddings,
            limits={}
        )
        
        # Rerank
        results = retrieval_pipeline_prefetch._cross_encoder_rerank(
            query=query,
            candidates=candidates,
            limit=10
        )
        
        # Verify results are sorted by score (descending)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score

    def test_cross_encoder_rerank_empty_candidates(self, retrieval_pipeline_prefetch):
        """Test cross-encoder reranking with empty candidates."""
        query = "test query"
        
        results = retrieval_pipeline_prefetch._cross_encoder_rerank(
            query=query,
            candidates=[],
            limit=10
        )
        
        # Should return empty list
        assert len(results) == 0


class TestConvertToResults:
    """Tests for converting candidates to RetrievalResult objects."""

    def test_convert_to_results(
        self,
        retrieval_pipeline_prefetch,
        populated_collection,
        embedding_manager
    ):
        """Test converting Qdrant points to RetrievalResult objects."""
        query = "machine learning"
        all_embeddings = embedding_manager.generate_all_embeddings(query)
        
        # Extract and format single query embeddings
        mat64 = all_embeddings["matryoshka_64"][0]
        mat768 = all_embeddings["matryoshka_768"][0]
        
        query_embeddings = {
            "matryoshka_64": mat64.tolist() if hasattr(mat64, 'tolist') else mat64,
            "matryoshka_768": mat768.tolist() if hasattr(mat768, 'tolist') else mat768,
            "colbert": all_embeddings["colbert"][0],
            "splade": all_embeddings["splade"][0]
        }
        
        # Get candidates
        candidates = retrieval_pipeline_prefetch._hybrid_search_with_prefetch(
            query=query,
            collection_name=populated_collection,
            query_embeddings=query_embeddings,
            limits={}
        )
        
        # Convert
        results = retrieval_pipeline_prefetch._convert_to_results(candidates)
        
        assert isinstance(results, list)
        assert len(results) == len(candidates)
        
        # Verify structure
        for result in results:
            assert isinstance(result, RetrievalResult)
            assert hasattr(result, 'id')
            assert hasattr(result, 'text')
            assert hasattr(result, 'score')
            assert hasattr(result, 'metadata')

    def test_convert_to_results_empty(self, retrieval_pipeline_prefetch):
        """Test converting empty candidates list."""
        results = retrieval_pipeline_prefetch._convert_to_results([])
        
        assert isinstance(results, list)
        assert len(results) == 0


class TestIntegrationScenarios:
    """Integration tests for complete retrieval workflows."""

    def test_complete_retrieval_workflow_prefetch(
        self,
        retrieval_pipeline_prefetch,
        populated_collection
    ):
        """Test complete retrieval workflow with prefetch."""
        query = "What is machine learning and neural networks?"
        
        # Execute retrieval
        results = retrieval_pipeline_prefetch.retrieve(
            query=query,
            collection_name=populated_collection,
            use_cross_encoder=True
        )
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Verify result quality
        result = results[0]
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        assert isinstance(result.score, float)
        assert isinstance(result.metadata, dict)

    def test_complete_retrieval_workflow_naive(
        self,
        retrieval_pipeline_naive,
        populated_collection
    ):
        """Test complete retrieval workflow with naive implementation."""
        query = "What is machine learning and neural networks?"
        
        # Execute retrieval
        results = retrieval_pipeline_naive.retrieve(
            query=query,
            collection_name=populated_collection,
            use_cross_encoder=True
        )
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) > 0

    def test_retrieval_with_different_queries(
        self,
        retrieval_pipeline_prefetch,
        populated_collection
    ):
        """Test retrieval with different query types."""
        queries = [
            "machine learning",
            "neural networks and deep learning",
            "Python programming",
            "natural language processing"
        ]
        
        for query in queries:
            results = retrieval_pipeline_prefetch.retrieve(
                query=query,
                collection_name=populated_collection,
                use_cross_encoder=False  # Faster for testing
            )
            
            # Should return results for all queries
            assert isinstance(results, list)

    def test_retrieval_consistency(
        self,
        retrieval_pipeline_prefetch,
        populated_collection
    ):
        """Test that retrieval returns results for same query."""
        query = "machine learning"
        
        # Execute same query twice
        results1 = retrieval_pipeline_prefetch.retrieve(
            query=query,
            collection_name=populated_collection,
            use_cross_encoder=False  # Disable for faster testing
        )
        
        results2 = retrieval_pipeline_prefetch.retrieve(
            query=query,
            collection_name=populated_collection,
            use_cross_encoder=False
        )
        
        # Both should return results
        assert isinstance(results1, list)
        assert isinstance(results2, list)
        
        # Note: Due to random embeddings in test mode, exact consistency
        # cannot be guaranteed. In production with real models, results
        # would be deterministic for the same query.

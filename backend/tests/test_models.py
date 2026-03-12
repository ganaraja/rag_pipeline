"""
Tests for Pydantic models.

Validates that all data models have proper validation and constraints.
"""

import pytest
from pydantic import ValidationError

from models import (
    CreateCollectionRequest,
    CreateCollectionResponse,
    DeleteCollectionResponse,
    DocumentChunk,
    ParentChunk,
    SemanticChunk,
    ContextualChunk,
    LateChunk,
    UploadResponse,
    QueryRequest,
    RetrievalResult,
    QueryResponse,
    SparseVector,
    MultiVectorEmbedding,
    AllEmbeddings,
)


class TestCollectionModels:
    """Tests for collection management models."""

    def test_create_collection_request_valid(self):
        """Test valid collection creation request."""
        request = CreateCollectionRequest(collection_name="test_collection")
        assert request.collection_name == "test_collection"

    def test_create_collection_request_empty_name(self):
        """Test that empty collection name is rejected."""
        with pytest.raises(ValidationError):
            CreateCollectionRequest(collection_name="")

    def test_create_collection_request_max_length(self):
        """Test that collection name exceeding max length is rejected."""
        with pytest.raises(ValidationError):
            CreateCollectionRequest(collection_name="a" * 256)

    def test_create_collection_request_serialization(self):
        """Test serialization and deserialization of collection request."""
        request = CreateCollectionRequest(collection_name="test_collection")
        serialized = request.model_dump()
        assert serialized == {"collection_name": "test_collection"}
        deserialized = CreateCollectionRequest.model_validate(serialized)
        assert deserialized.collection_name == "test_collection"

    def test_create_collection_response(self):
        """Test collection creation response."""
        response = CreateCollectionResponse(
            success=True,
            collection_name="test_collection",
            message="Collection created successfully"
        )
        assert response.success is True
        assert response.collection_name == "test_collection"
        assert response.message == "Collection created successfully"

    def test_create_collection_response_serialization(self):
        """Test serialization of collection response."""
        response = CreateCollectionResponse(
            success=True,
            collection_name="test_collection",
            message="Success"
        )
        serialized = response.model_dump()
        assert serialized["success"] is True
        assert serialized["collection_name"] == "test_collection"

    def test_delete_collection_response(self):
        """Test collection deletion response."""
        response = DeleteCollectionResponse(success=True, message="Deleted")
        assert response.success is True


class TestDocumentChunkModels:
    """Tests for document chunk models."""

    def test_document_chunk_valid(self):
        """Test valid document chunk creation."""
        chunk = DocumentChunk(
            chunk_id=1,
            parent_id=0,
            text="This is a test chunk",
            start_char=0,
            end_char=20,
            metadata={"source": "test.pdf"}
        )
        assert chunk.chunk_id == 1
        assert chunk.text == "This is a test chunk"
        assert chunk.metadata["source"] == "test.pdf"

    def test_document_chunk_empty_text(self):
        """Test that empty text is rejected."""
        with pytest.raises(ValidationError):
            DocumentChunk(
                chunk_id=1,
                parent_id=0,
                text="",
                start_char=0,
                end_char=0
            )

    def test_document_chunk_negative_positions(self):
        """Test that negative positions are rejected."""
        with pytest.raises(ValidationError):
            DocumentChunk(
                chunk_id=1,
                parent_id=0,
                text="test",
                start_char=-1,
                end_char=10
            )

    def test_document_chunk_boundary_positions(self):
        """Test boundary values for character positions."""
        chunk = DocumentChunk(
            chunk_id=1,
            parent_id=0,
            text="test",
            start_char=0,
            end_char=0
        )
        assert chunk.start_char == 0
        assert chunk.end_char == 0

    def test_document_chunk_serialization(self):
        """Test serialization and deserialization of document chunk."""
        chunk = DocumentChunk(
            chunk_id=1,
            parent_id=0,
            text="test chunk",
            start_char=0,
            end_char=10,
            metadata={"key": "value"}
        )
        serialized = chunk.model_dump()
        deserialized = DocumentChunk.model_validate(serialized)
        assert deserialized.chunk_id == chunk.chunk_id
        assert deserialized.text == chunk.text
        assert deserialized.metadata == chunk.metadata

    def test_parent_chunk_valid(self):
        """Test valid parent chunk creation."""
        chunk = ParentChunk(
            id=1,
            text="Parent chunk text",
            section_title="Introduction"
        )
        assert chunk.id == 1
        assert chunk.section_title == "Introduction"

    def test_semantic_chunk_valid(self):
        """Test valid semantic chunk creation."""
        chunk = SemanticChunk(
            id=1,
            parent_id=0,
            text="Semantic chunk text",
            start_index=0,
            end_index=19
        )
        assert chunk.id == 1
        assert chunk.parent_id == 0

    def test_semantic_chunk_negative_indices(self):
        """Test that negative indices are rejected."""
        with pytest.raises(ValidationError):
            SemanticChunk(
                id=1,
                parent_id=0,
                text="test",
                start_index=-1,
                end_index=10
            )

    def test_semantic_chunk_serialization(self):
        """Test serialization of semantic chunk."""
        chunk = SemanticChunk(
            id=1,
            parent_id=0,
            text="test",
            start_index=0,
            end_index=4
        )
        serialized = chunk.model_dump()
        deserialized = SemanticChunk.model_validate(serialized)
        assert deserialized.id == chunk.id
        assert deserialized.text == chunk.text

    def test_contextual_chunk_valid(self):
        """Test valid contextual chunk creation."""
        chunk = ContextualChunk(
            semantic_chunk_id=1,
            parent_id=0,
            semantic_chunk="Original text",
            parent_chunk="Parent context",
            contextual_chunk="Enriched text with context"
        )
        assert chunk.semantic_chunk_id == 1
        assert chunk.contextual_chunk == "Enriched text with context"

    def test_contextual_chunk_empty_text(self):
        """Test that empty contextual chunk text is rejected."""
        with pytest.raises(ValidationError):
            ContextualChunk(
                semantic_chunk_id=1,
                parent_id=0,
                semantic_chunk="Original",
                parent_chunk="Parent",
                contextual_chunk=""
            )

    def test_late_chunk_valid(self):
        """Test valid late chunk creation."""
        chunk = LateChunk(
            semantic_id=1,
            parent_id=0,
            text="Late chunk text",
            embedding=[0.1, 0.2, 0.3],
            num_tokens=5
        )
        assert chunk.semantic_id == 1
        assert len(chunk.embedding) == 3
        assert chunk.num_tokens == 5

    def test_late_chunk_zero_tokens(self):
        """Test that zero tokens is rejected."""
        with pytest.raises(ValidationError):
            LateChunk(
                semantic_id=1,
                parent_id=0,
                text="text",
                embedding=[0.1],
                num_tokens=0
            )

    def test_late_chunk_negative_tokens(self):
        """Test that negative tokens is rejected."""
        with pytest.raises(ValidationError):
            LateChunk(
                semantic_id=1,
                parent_id=0,
                text="text",
                embedding=[0.1],
                num_tokens=-1
            )

    def test_late_chunk_empty_embedding(self):
        """Test that empty embedding is rejected."""
        with pytest.raises(ValidationError):
            LateChunk(
                semantic_id=1,
                parent_id=0,
                text="text",
                embedding=[],
                num_tokens=1
            )


class TestUploadModels:
    """Tests for upload models."""

    def test_upload_response_valid(self):
        """Test valid upload response."""
        response = UploadResponse(
            success=True,
            chunks_created=10,
            processing_time=2.5,
            message="Upload successful"
        )
        assert response.success is True
        assert response.chunks_created == 10
        assert response.processing_time == 2.5

    def test_upload_response_negative_chunks(self):
        """Test that negative chunks is rejected."""
        with pytest.raises(ValidationError):
            UploadResponse(
                success=True,
                chunks_created=-1,
                processing_time=1.0
            )

    def test_upload_response_negative_time(self):
        """Test that negative processing time is rejected."""
        with pytest.raises(ValidationError):
            UploadResponse(
                success=True,
                chunks_created=10,
                processing_time=-1.0
            )

    def test_upload_response_boundary_values(self):
        """Test boundary values for upload response."""
        response = UploadResponse(
            success=False,
            chunks_created=0,
            processing_time=0.0
        )
        assert response.chunks_created == 0
        assert response.processing_time == 0.0


class TestQueryModels:
    """Tests for query models."""

    def test_query_request_valid(self):
        """Test valid query request."""
        request = QueryRequest(
            query="What is RAG?",
            collection_name="test_collection"
        )
        assert request.query == "What is RAG?"
        assert request.collection_name == "test_collection"

    def test_query_request_empty_query(self):
        """Test that empty query is rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(query="", collection_name="test")

    def test_query_request_empty_collection(self):
        """Test that empty collection name is rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(query="test query", collection_name="")

    def test_query_request_serialization(self):
        """Test serialization of query request."""
        request = QueryRequest(query="test", collection_name="col")
        serialized = request.model_dump()
        deserialized = QueryRequest.model_validate(serialized)
        assert deserialized.query == request.query
        assert deserialized.collection_name == request.collection_name

    def test_retrieval_result_valid(self):
        """Test valid retrieval result."""
        result = RetrievalResult(
            id=1,
            text="Retrieved text",
            score=0.95,
            distance=0.05,
            metadata={"source": "doc1"}
        )
        assert result.id == 1
        assert result.score == 0.95

    def test_query_response_valid(self):
        """Test valid query response."""
        sources = [
            RetrievalResult(
                id=1,
                text="Source 1",
                score=0.9,
                distance=0.1,
                metadata={}
            )
        ]
        response = QueryResponse(
            answer="This is the answer",
            sources=sources,
            retrieval_time=0.5,
            generation_time=1.2
        )
        assert response.answer == "This is the answer"
        assert len(response.sources) == 1
        assert response.retrieval_time == 0.5

    def test_query_response_negative_times(self):
        """Test that negative times are rejected."""
        with pytest.raises(ValidationError):
            QueryResponse(
                answer="test",
                sources=[],
                retrieval_time=-1.0,
                generation_time=1.0
            )

    def test_query_response_serialization(self):
        """Test serialization of query response."""
        response = QueryResponse(
            answer="test answer",
            sources=[],
            retrieval_time=0.5,
            generation_time=1.0
        )
        serialized = response.model_dump()
        deserialized = QueryResponse.model_validate(serialized)
        assert deserialized.answer == response.answer
        assert deserialized.retrieval_time == response.retrieval_time


class TestEmbeddingModels:
    """Tests for embedding models."""

    def test_sparse_vector_valid(self):
        """Test valid sparse vector."""
        sparse = SparseVector(
            indices=[0, 5, 10],
            values=[0.5, 0.3, 0.8]
        )
        assert len(sparse.indices) == 3
        assert len(sparse.values) == 3

    def test_sparse_vector_mismatched_lengths(self):
        """Test that mismatched indices and values are rejected."""
        with pytest.raises(ValidationError):
            SparseVector(
                indices=[0, 1, 2],
                values=[0.5, 0.3]
            )

    def test_multi_vector_embedding_valid(self):
        """Test valid multi-vector embedding."""
        multi = MultiVectorEmbedding(
            vectors=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        )
        assert len(multi.vectors) == 3
        assert len(multi.vectors[0]) == 2

    def test_multi_vector_embedding_empty(self):
        """Test that empty vectors are rejected."""
        with pytest.raises(ValidationError):
            MultiVectorEmbedding(vectors=[])

    def test_all_embeddings_valid(self):
        """Test valid all embeddings container."""
        embeddings = AllEmbeddings(
            matryoshka_64=[0.1] * 64,
            matryoshka_768=[0.2] * 768,
            colbert=[[0.3] * 128],
            splade=SparseVector(indices=[0, 1], values=[0.5, 0.6])
        )
        assert len(embeddings.matryoshka_64) == 64
        assert len(embeddings.matryoshka_768) == 768
        assert len(embeddings.colbert) == 1

    def test_all_embeddings_wrong_dimensions(self):
        """Test that wrong dimensions are rejected."""
        with pytest.raises(ValidationError):
            AllEmbeddings(
                matryoshka_64=[0.1] * 32,  # Wrong size
                matryoshka_768=[0.2] * 768,
                colbert=[[0.3] * 128],
                splade=SparseVector(indices=[0], values=[0.5])
            )

    def test_all_embeddings_serialization(self):
        """Test serialization of all embeddings."""
        embeddings = AllEmbeddings(
            matryoshka_64=[0.1] * 64,
            matryoshka_768=[0.2] * 768,
            colbert=[[0.3] * 128],
            splade=SparseVector(indices=[0, 1], values=[0.5, 0.6])
        )
        serialized = embeddings.model_dump()
        deserialized = AllEmbeddings.model_validate(serialized)
        assert len(deserialized.matryoshka_64) == 64
        assert len(deserialized.matryoshka_768) == 768
        assert len(deserialized.colbert) == 1

    def test_all_embeddings_wrong_matryoshka_768_size(self):
        """Test that wrong matryoshka_768 size is rejected."""
        with pytest.raises(ValidationError):
            AllEmbeddings(
                matryoshka_64=[0.1] * 64,
                matryoshka_768=[0.2] * 500,  # Wrong size
                colbert=[[0.3] * 128],
                splade=SparseVector(indices=[0], values=[0.5])
            )

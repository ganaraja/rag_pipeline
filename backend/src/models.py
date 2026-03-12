"""
Pydantic models for RAG Full-Stack Application.

This module defines all data structures used throughout the backend,
including collection management, document chunking, embeddings, and query models.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# Collection Management Models

class CreateCollectionRequest(BaseModel):
    """Request model for creating a new collection."""
    collection_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the collection to create"
    )


class CreateCollectionResponse(BaseModel):
    """Response model for collection creation."""
    success: bool = Field(..., description="Whether the operation succeeded")
    collection_name: str = Field(..., description="Name of the created collection")
    message: Optional[str] = Field(None, description="Optional message with additional details")


class DeleteCollectionResponse(BaseModel):
    """Response model for collection deletion."""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: Optional[str] = Field(None, description="Optional message with additional details")


# Document Chunk Models

class DocumentChunk(BaseModel):
    """Represents a processed document chunk with metadata."""
    chunk_id: int = Field(..., description="Unique identifier for this chunk")
    parent_id: int = Field(..., description="ID of the parent chunk")
    text: str = Field(..., min_length=1, description="Text content of the chunk")
    start_char: int = Field(..., ge=0, description="Starting character position in original document")
    end_char: int = Field(..., ge=0, description="Ending character position in original document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ParentChunk(BaseModel):
    """Represents a parent chunk extracted by Docling."""
    id: int = Field(..., description="Unique identifier for this parent chunk")
    text: str = Field(..., min_length=1, description="Text content of the parent chunk")
    section_title: Optional[str] = Field(None, description="Title of the section if available")


class SemanticChunk(BaseModel):
    """Represents a semantic chunk created by Chonkie."""
    id: int = Field(..., description="Unique identifier for this semantic chunk")
    parent_id: int = Field(..., description="ID of the parent chunk this belongs to")
    text: str = Field(..., min_length=1, description="Text content of the semantic chunk")
    start_index: int = Field(..., ge=0, description="Starting index within parent chunk")
    end_index: int = Field(..., ge=0, description="Ending index within parent chunk")


class ContextualChunk(BaseModel):
    """Represents a chunk enriched with LLM-generated context."""
    semantic_chunk_id: int = Field(..., description="ID of the semantic chunk")
    parent_id: int = Field(..., description="ID of the parent chunk")
    semantic_chunk: str = Field(..., min_length=1, description="Original semantic chunk text")
    parent_chunk: str = Field(..., min_length=1, description="Parent chunk text for context")
    contextual_chunk: str = Field(..., min_length=1, description="LLM-enriched chunk with context")


class LateChunk(BaseModel):
    """Represents a chunk with late chunking embeddings from Jina."""
    semantic_id: int = Field(..., description="ID of the semantic chunk")
    parent_id: int = Field(..., description="ID of the parent chunk")
    text: str = Field(..., min_length=1, description="Text content of the chunk")
    embedding: List[float] = Field(..., min_length=1, description="Jina embedding vector")
    num_tokens: int = Field(..., gt=0, description="Number of tokens in the chunk")


# Upload Models

class UploadResponse(BaseModel):
    """Response model for document upload."""
    success: bool = Field(..., description="Whether the upload succeeded")
    chunks_created: int = Field(..., ge=0, description="Number of chunks created from the document")
    processing_time: float = Field(..., ge=0.0, description="Time taken to process the document in seconds")
    message: Optional[str] = Field(None, description="Optional message with additional details")


# Query Models

class QueryRequest(BaseModel):
    """Request model for querying the RAG system."""
    query: str = Field(..., min_length=1, description="User query text")
    collection_name: str = Field(..., min_length=1, description="Name of the collection to query")


class RetrievalResult(BaseModel):
    """Represents a single retrieval result."""
    id: int = Field(..., description="Unique identifier of the retrieved chunk")
    text: str = Field(..., description="Text content of the retrieved chunk")
    score: float = Field(..., description="Relevance score")
    distance: float = Field(..., description="Distance metric from query")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class QueryResponse(BaseModel):
    """Response model for query results."""
    answer: str = Field(..., description="Generated answer from the LLM")
    sources: List[RetrievalResult] = Field(..., description="Retrieved source chunks")
    retrieval_time: float = Field(..., ge=0.0, description="Time taken for retrieval in seconds")
    generation_time: float = Field(..., ge=0.0, description="Time taken for answer generation in seconds")


# Embedding Models

class SparseVector(BaseModel):
    """Represents a sparse vector for SPLADE embeddings."""
    indices: List[int] = Field(..., description="Indices of non-zero values")
    values: List[float] = Field(..., description="Non-zero values")

    def model_post_init(self, __context: Any) -> None:
        """Validate that indices and values have the same length."""
        if len(self.indices) != len(self.values):
            raise ValueError("indices and values must have the same length")


class MultiVectorEmbedding(BaseModel):
    """Represents multi-vector embeddings for ColBERT."""
    vectors: List[List[float]] = Field(..., min_length=1, description="List of token-level vectors")


class AllEmbeddings(BaseModel):
    """Container for all embedding types for a chunk."""
    matryoshka_64: List[float] = Field(..., min_length=64, max_length=64, description="64-dimensional Matryoshka embedding")
    matryoshka_768: List[float] = Field(..., min_length=768, max_length=768, description="768-dimensional Matryoshka embedding")
    colbert: List[List[float]] = Field(..., min_length=1, description="ColBERT multi-vector embeddings")
    splade: SparseVector = Field(..., description="SPLADE sparse vector embedding")

"""
Generic Pydantic models for AI application API.

These models provide the basic structure for collection management.
Extend with your custom models as needed.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# Collection Management Models (Reusable)

class CreateCollectionRequest(BaseModel):
    """Request model for creating a collection."""
    collection_name: str = Field(..., min_length=1, description="Name of the collection to create")
    vector_size: Optional[int] = Field(768, description="Dimension of vectors (default: 768)")
    distance: Optional[str] = Field("Cosine", description="Distance metric (default: Cosine)")


class CreateCollectionResponse(BaseModel):
    """Response model for collection creation."""
    success: bool
    collection_name: str
    message: str


class DeleteCollectionResponse(BaseModel):
    """Response model for collection deletion."""
    success: bool
    message: str


class ListCollectionsResponse(BaseModel):
    """Response model for listing collections."""
    collections: List[str]
    count: int


class CollectionInfoResponse(BaseModel):
    """Response model for collection information."""
    name: str
    points_count: int
    vectors_config: Optional[Dict[str, Any]] = None
    sparse_vectors_config: Optional[Dict[str, Any]] = None


# Document Chunk Models

class DocumentChunk(BaseModel):
    """Model for a document chunk."""
    id: str = Field(..., description="Unique identifier for the chunk")
    text: str = Field(..., description="Text content of the chunk")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata for the chunk")


class StorePointsRequest(BaseModel):
    """Request model for storing points."""
    collection_name: str = Field(..., description="Target collection name")
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    chunks: List[DocumentChunk] = Field(..., description="List of document chunks")


class StorePointsResponse(BaseModel):
    """Response model for storing points."""
    success: bool
    points_stored: int
    message: str


# Search Models

class SearchRequest(BaseModel):
    """Request model for searching."""
    collection_name: str = Field(..., description="Collection to search")
    query_vector: List[float] = Field(..., description="Query embedding vector")
    limit: Optional[int] = Field(10, description="Number of results to return")


class SearchResult(BaseModel):
    """Model for a search result."""
    id: str = Field(..., description="Result ID")
    score: Optional[float] = Field(None, description="Similarity score")
    text: str = Field(..., description="Text content")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata")


class SearchResponse(BaseModel):
    """Response model for search."""
    results: List[SearchResult]
    count: int
    collection_name: str


# Health Check Models

class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    qdrant_accessible: bool
    message: str


# Error Models

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    detail: Optional[str] = None
    status_code: int


# TODO: Add your custom models below
# Example:
# class YourCustomRequest(BaseModel):
#     field1: str
#     field2: int
#
# class YourCustomResponse(BaseModel):
#     success: bool
#     data: dict
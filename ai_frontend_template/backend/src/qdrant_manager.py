"""
Generic Qdrant database manager for AI applications.

This module provides a simplified QdrantManager class that can be extended
for specific AI applications. It includes basic collection management and
vector operations.
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
)


class QdrantManager:
    """
    Manages Qdrant vector database operations.
    
    This is a generic implementation that can be extended for specific use cases.
    """

    def __init__(self, path: str = "./qdrant_db"):
        """
        Initialize Qdrant client.

        Args:
            path: Path to Qdrant database directory
        """
        self.client = QdrantClient(path=path)

    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 768,
        distance: Distance = Distance.COSINE
    ) -> None:
        """
        Create a collection with basic vector configuration.
        
        Override this method to add custom vector configurations
        (multi-vectors, sparse vectors, etc.)

        Args:
            collection_name: Name of collection to create
            vector_size: Dimension of vectors (default: 768)
            distance: Distance metric (default: COSINE)

        Raises:
            ValueError: If collection already exists
        """
        # Check if collection already exists
        collections = self.client.get_collections().collections
        if any(col.name == collection_name for col in collections):
            raise ValueError(f"Collection '{collection_name}' already exists")

        # Create collection with basic configuration
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=distance
            )
        )

    def list_collections(self) -> List[str]:
        """
        List all collection names.

        Returns:
            List of collection names
        """
        collections = self.client.get_collections().collections
        return [col.name for col in collections]

    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection.

        Args:
            collection_name: Name of collection to delete

        Raises:
            ValueError: If collection doesn't exist
        """
        collections = self.list_collections()
        if collection_name not in collections:
            raise ValueError(f"Collection '{collection_name}' does not exist")

        self.client.delete_collection(collection_name=collection_name)

    def store_points(
        self,
        collection_name: str,
        points: List[PointStruct]
    ) -> None:
        """
        Store points in a collection.
        
        Override this method for custom point storage logic.

        Args:
            collection_name: Target collection
            points: List of PointStruct objects to store

        Raises:
            ValueError: If collection doesn't exist
        """
        collections = self.list_collections()
        if collection_name not in collections:
            raise ValueError(f"Collection '{collection_name}' does not exist")

        # Upload points to Qdrant
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10
    ) -> List[Any]:
        """
        Search for similar vectors in a collection.
        
        Override this method for custom search logic (multi-stage, hybrid, etc.)

        Args:
            collection_name: Collection to search
            query_vector: Query embedding vector
            limit: Number of results to return

        Returns:
            List of scored points with payloads
        """
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        return results

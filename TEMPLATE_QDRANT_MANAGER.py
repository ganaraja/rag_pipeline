"""
Generic Qdrant database manager for AI applications.

This is a simplified, generic implementation that can be extended
for specific AI applications.

Supports both embedded mode (local storage) and server mode (remote Qdrant).
"""

import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models


class QdrantManager:
    """
    Manages Qdrant vector database operations.
    
    This is a generic implementation that can be extended for specific use cases.
    Supports both embedded mode and server mode.
    """

    def __init__(
        self,
        mode: str = "embedded",
        path: str = "./qdrant_db",
        host: str = "localhost",
        port: str = "6333",
        api_key: Optional[str] = None
    ):
        """
        Initialize Qdrant client.

        Args:
            mode: "embedded" for local storage or "server" for remote Qdrant
            path: Path to Qdrant database directory (embedded mode only)
            host: Qdrant server host (server mode only)
            port: Qdrant server port (server mode only)
            api_key: Optional API key for Qdrant Cloud (server mode only)
        """
        if mode == "embedded":
            self.client = QdrantClient(path=path)
        elif mode == "server":
            if api_key:
                self.client = QdrantClient(url=f"https://{host}:{port}", api_key=api_key)
            else:
                self.client = QdrantClient(url=f"http://{host}:{port}")
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'embedded' or 'server'")

    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 768,
        distance: str = "Cosine"
    ) -> None:
        """
        Create a collection with basic vector configuration.
        
        Override this method to add custom vector configurations
        (multi-vectors, sparse vectors, etc.)

        Args:
            collection_name: Name of collection to create
            vector_size: Dimension of vectors (default: 768)
            distance: Distance metric (default: "Cosine")

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
            vectors_config=rest_models.VectorParams(
                size=vector_size,
                distance=rest_models.Distance.COSINE
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
        embeddings: List[List[float]],
        chunks: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> None:
        """
        Store points in a collection with batching support.
        
        Override this method for custom point storage logic.

        Args:
            collection_name: Target collection
            embeddings: List of embedding vectors
            chunks: List of chunk dicts with keys: id, text, meta
            batch_size: Number of points to upsert per batch

        Raises:
            ValueError: If collection doesn't exist or embeddings length mismatch
        """
        collections = self.list_collections()
        if collection_name not in collections:
            raise ValueError(f"Collection '{collection_name}' does not exist")

        if len(embeddings) != len(chunks):
            raise ValueError("Number of embeddings must match number of chunks")

        # Prepare all points
        all_points = []
        for emb, chunk in zip(embeddings, chunks):
            # Use chunk ID or generate one
            point_id = chunk.get("id", str(uuid.uuid4()))
            
            # Try to convert to int if possible (Qdrant prefers int IDs)
            try:
                if isinstance(point_id, str) and point_id.isdigit():
                    point_id = int(point_id)
            except Exception:
                pass

            all_points.append(
                rest_models.PointStruct(
                    id=point_id,
                    vector=list(emb),
                    payload={
                        "text": chunk.get("text", ""),
                        "meta": chunk.get("meta", {})
                    }
                )
            )

        # Upload points to Qdrant in batches
        total_points = len(all_points)
        for i in range(0, total_points, batch_size):
            batch_points = all_points[i:i + batch_size]
            self.client.upsert(
                collection_name=collection_name,
                points=batch_points
            )

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in a collection.
        
        Override this method for custom search logic (multi-stage, hybrid, etc.)

        Args:
            collection_name: Collection to search
            query_vector: Query embedding vector
            limit: Number of results to return

        Returns:
            List of dicts with keys: id, score, text, meta
        """
        # Use query_points (modern Qdrant API)
        response = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        # Extract results from QueryResponse
        results = response.points if hasattr(response, 'points') else []
        
        # Format results
        out = []
        for point in results:
            payload = point.payload if hasattr(point, 'payload') else {}
            score = point.score if hasattr(point, 'score') else None
            point_id = point.id if hasattr(point, 'id') else None

            text = payload.get('text', '')
            meta = payload.get('meta', {})
            
            if text:
                out.append({
                    'id': str(point_id) if point_id is not None else '',
                    'score': float(score) if score is not None else None,
                    'text': text,
                    'meta': meta
                })
        
        return out

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a collection.

        Args:
            collection_name: Name of collection

        Returns:
            Dictionary with collection information
        """
        try:
            collection_info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "points_count": collection_info.points_count,
                "vectors_config": collection_info.config.params.vectors,
                "sparse_vectors_config": collection_info.config.params.sparse_vectors
            }
        except Exception as e:
            raise ValueError(f"Failed to get collection info for '{collection_name}': {e}")

    def health_check(self) -> bool:
        """
        Check if Qdrant is accessible.

        Returns:
            True if Qdrant is accessible, False otherwise
        """
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False

"""
Qdrant database manager for RAG Full-Stack Application.

This module provides the QdrantManager class for managing Qdrant vector database operations,
including collection creation with multi-vector configuration, point storage, and multi-stage retrieval.
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    SparseVector as QdrantSparseVector,
    SparseVectorParams,
    SparseIndexParams,
    Modifier,
    MultiVectorConfig,
    MultiVectorComparator,
    HnswConfigDiff,
    NamedVector,
    NamedSparseVector,
    Prefetch,
    QueryRequest,
    Query,
)
from models import DocumentChunk, SparseVector


class QdrantManager:
    """
    Manages Qdrant vector database operations.

    Handles:
    - Collection creation with multi-vector configuration
    - Point storage with multiple embedding types
    - Multi-stage retrieval with prefetch
    """

    def __init__(self, path: str = "./qdrant_db"):
        """
        Initialize Qdrant client.

        Args:
            path: Path to Qdrant database directory
        """
        self.client = QdrantClient(path=path)

    def create_collection(self, collection_name: str) -> None:
        """
        Create collection with multi-vector configuration.

        Configuration:
        - matryoshka_64: 64D dense vectors (COSINE)
        - matryoshka_768: 768D dense vectors (COSINE)
        - colbert: 128D multi-vectors (MAX_SIM comparator)
        - splade: Sparse vectors (IDF modifier)

        Args:
            collection_name: Name of collection to create

        Raises:
            ValueError: If collection already exists
        """
        # Check if collection already exists
        collections = self.client.get_collections().collections
        if any(col.name == collection_name for col in collections):
            raise ValueError(f"Collection '{collection_name}' already exists")

        # Create collection with multi-vector configuration
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "matryoshka_64": VectorParams(
                    size=64,
                    distance=Distance.COSINE
                ),
                "matryoshka_768": VectorParams(
                    size=768,
                    distance=Distance.COSINE
                ),
                "colbert": VectorParams(
                    size=128,
                    distance=Distance.COSINE,
                    multivector_config=MultiVectorConfig(
                        comparator=MultiVectorComparator.MAX_SIM
                    ),
                    hnsw_config=HnswConfigDiff(
                        m=0  # Disable HNSW for reranking
                    )
                )
            },
            sparse_vectors_config={
                "splade": SparseVectorParams(
                    index=SparseIndexParams(
                        on_disk=False
                    ),
                    modifier=Modifier.IDF
                )
            }
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
        chunks: List[DocumentChunk],
        embeddings: Dict[str, Any]
    ) -> None:
        """
        Store document chunks with all embedding types.

        Args:
            collection_name: Target collection
            chunks: Document chunks with metadata
            embeddings: Dict containing all embedding types with keys:
                - matryoshka_64: List of 64D embeddings
                - matryoshka_768: List of 768D embeddings
                - colbert: List of multi-vector embeddings
                - splade: List of SparseVector objects

        Raises:
            ValueError: If collection doesn't exist or embeddings length mismatch
        """
        collections = self.list_collections()
        if collection_name not in collections:
            raise ValueError(f"Collection '{collection_name}' does not exist")

        # Validate embeddings length matches chunks
        num_chunks = len(chunks)
        if (len(embeddings.get("matryoshka_64", [])) != num_chunks or
            len(embeddings.get("matryoshka_768", [])) != num_chunks or
            len(embeddings.get("colbert", [])) != num_chunks or
            len(embeddings.get("splade", [])) != num_chunks):
            raise ValueError("Number of embeddings must match number of chunks")

        # Create points
        points = []
        for idx, chunk in enumerate(chunks):
            # Convert SparseVector to Qdrant format
            splade_embedding = embeddings["splade"][idx]
            qdrant_sparse = QdrantSparseVector(
                indices=splade_embedding.indices,
                values=splade_embedding.values
            )

            point = PointStruct(
                id=chunk.chunk_id,
                vector={
                    "matryoshka_64": embeddings["matryoshka_64"][idx],
                    "matryoshka_768": embeddings["matryoshka_768"][idx],
                    "colbert": embeddings["colbert"][idx]
                },
                payload={
                    "text": chunk.text,
                    "chunk_id": chunk.chunk_id,
                    "parent_id": chunk.parent_id,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "metadata": chunk.metadata
                }
            )
            
            # Add sparse vector separately
            point.vector["splade"] = qdrant_sparse
            points.append(point)

        # Upload points to Qdrant
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    def query_with_prefetch(
        self,
        collection_name: str,
        query_embeddings: Dict[str, Any],
        limits: Optional[Dict[str, int]] = None
    ) -> List[Any]:
        """
        Execute multi-stage retrieval using Qdrant prefetch.

        Stages:
        1. Matryoshka 64D (500 candidates)
        2. Matryoshka 768D refinement (100 candidates)
        3. SPLADE parallel retrieval (100 candidates)
        4. ColBERT merge and refinement (50 candidates)

        Args:
            collection_name: Collection to search
            query_embeddings: All query embedding types with keys:
                - matryoshka_64: 64D query embedding
                - matryoshka_768: 768D query embedding
                - colbert: ColBERT multi-vector query embedding
                - splade: SparseVector query embedding
            limits: Optional dict with limit for each stage. Defaults:
                - stage1_limit: 500 (matryoshka_64)
                - stage2_limit: 100 (matryoshka_768)
                - stage3_limit: 100 (splade)
                - stage4_limit: 50 (colbert)

        Returns:
            List of scored points with payloads
        """
        # Set default limits
        if limits is None:
            limits = {}
        stage1_limit = limits.get("stage1_limit", 500)
        stage2_limit = limits.get("stage2_limit", 100)
        stage3_limit = limits.get("stage3_limit", 100)
        stage4_limit = limits.get("stage4_limit", 50)

        # Convert SparseVector to Qdrant format
        splade_query = query_embeddings["splade"]
        qdrant_sparse_query = QdrantSparseVector(
            indices=splade_query.indices,
            values=splade_query.values
        )

        # Build prefetch query
        # Stage 1: Matryoshka 64D retrieval (500 candidates)
        prefetch_stage1 = Prefetch(
            query=query_embeddings["matryoshka_64"],
            using="matryoshka_64",
            limit=stage1_limit
        )

        # Stage 2: Matryoshka 768D refinement (100 candidates from stage 1)
        prefetch_stage2 = Prefetch(
            query=query_embeddings["matryoshka_768"],
            using="matryoshka_768",
            limit=stage2_limit,
            prefetch=[prefetch_stage1]
        )

        # Stage 3: SPLADE parallel retrieval (100 candidates)
        prefetch_stage3_splade = Prefetch(
            query=qdrant_sparse_query,
            using="splade",
            limit=stage3_limit
        )

        # Stage 4: ColBERT merge and refinement (50 candidates from merged results)
        results = self.client.query_points(
            collection_name=collection_name,
            query=query_embeddings["colbert"],
            using="colbert",
            limit=stage4_limit,
            prefetch=[prefetch_stage2, prefetch_stage3_splade]
        )

        return results.points

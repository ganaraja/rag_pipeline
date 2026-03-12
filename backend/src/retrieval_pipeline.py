"""
Multi-Embedding Retrieval Pipeline for RAG Full-Stack Application.

This module implements a sophisticated multi-stage retrieval pipeline that combines
multiple embedding strategies for optimal search accuracy and efficiency:

1. Matryoshka 64D: Initial broad retrieval (500 candidates)
2. Matryoshka 768D: Refined semantic search (100 candidates)
3. SPLADE: Sparse lexical retrieval with term expansion (100 candidates)
4. ColBERT: Late interaction multi-vector refinement (50 candidates)
5. Cross-encoder: Final precision reranking (20 results)

Two implementations are provided:
- Optimized with Qdrant prefetch (recommended)
- Naive sequential filtering (for comparison)
"""

from typing import List, Dict, Any, Optional
import logging
import time
from models import RetrievalResult
from qdrant_manager import QdrantManager
from embedding_manager import EmbeddingModelManager


# Configure logging
logger = logging.getLogger(__name__)


class MultiEmbeddingRetrievalPipeline:
    """
    Implements sophisticated multi-stage retrieval pipeline.

    This class orchestrates the complete retrieval process using multiple
    embedding types and strategies. It supports both an optimized implementation
    using Qdrant's prefetch feature and a naive sequential implementation for
    comparison purposes.

    Attributes:
        qdrant: QdrantManager instance for vector database operations
        embeddings: EmbeddingModelManager instance for generating embeddings
        use_prefetch: Whether to use optimized prefetch implementation
    """

    def __init__(
        self,
        qdrant_manager: QdrantManager,
        embedding_manager: EmbeddingModelManager,
        use_prefetch: bool = True
    ):
        """
        Initialize retrieval pipeline.

        Args:
            qdrant_manager: Qdrant database manager for vector operations
            embedding_manager: Embedding model manager for generating embeddings
            use_prefetch: Use optimized prefetch implementation (default: True)
        """
        self.qdrant = qdrant_manager
        self.embeddings = embedding_manager
        self.use_prefetch = use_prefetch
        
        logger.info(
            f"Initialized MultiEmbeddingRetrievalPipeline "
            f"(prefetch={'enabled' if use_prefetch else 'disabled'})"
        )

    def retrieve(
        self,
        query: str,
        collection_name: str,
        use_cross_encoder: bool = True,
        limits: Optional[Dict[str, int]] = None
    ) -> List[RetrievalResult]:
        """
        Execute complete retrieval pipeline.

        This method orchestrates the full multi-stage retrieval process:
        1. Generate all query embeddings
        2. Execute hybrid search (prefetch or naive)
        3. Optionally apply cross-encoder reranking
        4. Convert results to RetrievalResult objects

        Args:
            query: User query text
            collection_name: Collection to search
            use_cross_encoder: Apply final cross-encoder reranking (default: True)
            limits: Optional dict with limit for each stage. Defaults:
                - stage1_limit: 500 (matryoshka_64)
                - stage2_limit: 100 (matryoshka_768)
                - stage3_limit: 100 (splade)
                - stage4_limit: 50 (colbert)
                - final_limit: 20 (cross-encoder)

        Returns:
            List of RetrievalResult objects with scores and metadata

        Raises:
            ValueError: If collection doesn't exist or query is empty
            RuntimeError: If retrieval fails

        Example:
            >>> pipeline = MultiEmbeddingRetrievalPipeline(qdrant, embeddings)
            >>> results = pipeline.retrieve("What is Python?", "my_collection")
            >>> len(results)
            20
            >>> results[0].score > results[1].score
            True
        """
        if not query:
            raise ValueError("query cannot be empty")
        
        if collection_name not in self.qdrant.list_collections():
            raise ValueError(f"Collection '{collection_name}' does not exist")
        
        # Set default limits
        if limits is None:
            limits = {}
        final_limit = limits.get("final_limit", 20)
        
        logger.info(f"Starting retrieval for query: '{query[:50]}...' in collection: {collection_name}")
        start_time = time.time()
        
        # Stage 1-4: Generate query embeddings
        logger.info("Generating query embeddings...")
        embedding_start = time.time()
        all_embeddings = self.embeddings.generate_all_embeddings(query)
        
        # Extract single query embeddings from batch results and convert to proper format
        mat64 = all_embeddings["matryoshka_64"][0]
        mat768 = all_embeddings["matryoshka_768"][0]
        
        query_embeddings = {
            "matryoshka_64": mat64.tolist() if hasattr(mat64, 'tolist') else mat64,
            "matryoshka_768": mat768.tolist() if hasattr(mat768, 'tolist') else mat768,
            "colbert": all_embeddings["colbert"][0],
            "splade": all_embeddings["splade"][0]  # Extract first SparseVector
        }
        
        embedding_time = time.time() - embedding_start
        logger.info(f"Query embeddings generated in {embedding_time:.3f}s")
        
        # Stage 2-5: Execute hybrid search
        if self.use_prefetch:
            logger.info("Executing optimized hybrid search with prefetch...")
            candidates = self._hybrid_search_with_prefetch(
                query,
                collection_name,
                query_embeddings,
                limits
            )
        else:
            logger.info("Executing naive hybrid search...")
            candidates = self._hybrid_search_naive(
                query,
                collection_name,
                query_embeddings,
                limits
            )
        
        logger.info(f"Hybrid search returned {len(candidates)} candidates")
        
        # Stage 6: Optional cross-encoder reranking
        if use_cross_encoder and len(candidates) > 0:
            logger.info("Applying cross-encoder reranking...")
            results = self._cross_encoder_rerank(query, candidates, final_limit)
        else:
            # Convert candidates to RetrievalResult without reranking
            logger.info("Skipping cross-encoder reranking")
            results = self._convert_to_results(candidates[:final_limit])
        
        total_time = time.time() - start_time
        logger.info(
            f"Retrieval complete: {len(results)} results in {total_time:.3f}s "
            f"(embeddings: {embedding_time:.3f}s, search: {total_time - embedding_time:.3f}s)"
        )
        
        return results

    def _hybrid_search_with_prefetch(
        self,
        query: str,
        collection_name: str,
        query_embeddings: Dict[str, Any],
        limits: Dict[str, int]
    ) -> List[Any]:
        """
        Optimized retrieval using Qdrant prefetch.

        This method uses Qdrant's prefetch feature to efficiently execute
        multi-stage retrieval in a single query. The stages are:

        1. Matryoshka 64D: Broad retrieval (500 candidates)
        2. Matryoshka 768D: Refine stage 1 results (100 candidates)
        3. SPLADE: Parallel sparse retrieval (100 candidates)
        4. ColBERT: Merge and refine (50 candidates)

        Args:
            query: User query text
            collection_name: Collection to search
            query_embeddings: All query embedding types
            limits: Limits for each stage

        Returns:
            List of scored points from Qdrant

        Raises:
            RuntimeError: If search fails
        """
        logger.info("Stage 1-4: Executing prefetch-based hybrid search")
        search_start = time.time()
        
        try:
            results = self.qdrant.query_with_prefetch(
                collection_name=collection_name,
                query_embeddings=query_embeddings,
                limits=limits
            )
            
            search_time = time.time() - search_start
            logger.info(
                f"Prefetch search completed in {search_time:.3f}s: "
                f"{len(results)} candidates retrieved"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Prefetch search failed: {str(e)}")
            raise RuntimeError(f"Hybrid search with prefetch failed: {str(e)}")

    def _hybrid_search_naive(
        self,
        query: str,
        collection_name: str,
        query_embeddings: Dict[str, Any],
        limits: Dict[str, int]
    ) -> List[Any]:
        """
        Naive sequential retrieval for comparison.

        This method implements the same multi-stage retrieval logic but
        executes each stage sequentially with explicit filtering. This is
        less efficient than prefetch but useful for comparison and debugging.

        Stages:
        1. Matryoshka 64D: Initial retrieval (500 candidates)
        2. SPLADE: Parallel sparse retrieval (100 candidates)
        3. Matryoshka 768D: Refine stage 1 by filtering (100 candidates)
        4. Merge stages 2 and 3, refine with ColBERT (50 candidates)

        Args:
            query: User query text
            collection_name: Collection to search
            query_embeddings: All query embedding types
            limits: Limits for each stage

        Returns:
            List of scored points

        Raises:
            RuntimeError: If any stage fails
        """
        # Set default limits
        stage1_limit = limits.get("stage1_limit", 500)
        stage2_limit = limits.get("stage2_limit", 100)
        stage3_limit = limits.get("stage3_limit", 100)
        stage4_limit = limits.get("stage4_limit", 50)
        
        # Stage 1: Matryoshka 64D retrieval
        logger.info(f"Stage 1: Matryoshka 64D retrieval (limit={stage1_limit})")
        stage1_start = time.time()
        
        try:
            stage1_results = self.qdrant.client.query_points(
                collection_name=collection_name,
                query=query_embeddings["matryoshka_64"],
                using="matryoshka_64",
                limit=stage1_limit
            ).points
            
            stage1_time = time.time() - stage1_start
            logger.info(f"Stage 1 complete: {len(stage1_results)} candidates in {stage1_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Stage 1 failed: {str(e)}")
            raise RuntimeError(f"Stage 1 (Matryoshka 64D) failed: {str(e)}")
        
        # Stage 2: SPLADE retrieval (parallel)
        logger.info(f"Stage 2: SPLADE retrieval (limit={stage3_limit})")
        stage2_start = time.time()
        
        try:
            splade_query = query_embeddings["splade"]
            from qdrant_client.models import SparseVector as QdrantSparseVector
            
            qdrant_sparse_query = QdrantSparseVector(
                indices=splade_query.indices,
                values=splade_query.values
            )
            
            stage2_results = self.qdrant.client.query_points(
                collection_name=collection_name,
                query=qdrant_sparse_query,
                using="splade",
                limit=stage3_limit
            ).points
            
            stage2_time = time.time() - stage2_start
            logger.info(f"Stage 2 complete: {len(stage2_results)} candidates in {stage2_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Stage 2 failed: {str(e)}")
            raise RuntimeError(f"Stage 2 (SPLADE) failed: {str(e)}")
        
        # Stage 3: Matryoshka 768D refinement of stage 1 results
        logger.info(f"Stage 3: Matryoshka 768D refinement (limit={stage2_limit})")
        stage3_start = time.time()
        
        try:
            # Extract IDs from stage 1 for filtering
            stage1_ids = [point.id for point in stage1_results]
            
            # Query with 768D embeddings, filtering to stage 1 IDs
            from qdrant_client.models import Filter, FieldCondition, MatchAny
            
            stage3_results = self.qdrant.client.query_points(
                collection_name=collection_name,
                query=query_embeddings["matryoshka_768"],
                using="matryoshka_768",
                limit=stage2_limit,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chunk_id",
                            match=MatchAny(any=stage1_ids)
                        )
                    ]
                )
            ).points
            
            stage3_time = time.time() - stage3_start
            logger.info(f"Stage 3 complete: {len(stage3_results)} candidates in {stage3_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Stage 3 failed: {str(e)}")
            raise RuntimeError(f"Stage 3 (Matryoshka 768D refinement) failed: {str(e)}")
        
        # Stage 4: Merge and ColBERT refinement
        logger.info(f"Stage 4: Merge and ColBERT refinement (limit={stage4_limit})")
        stage4_start = time.time()
        
        try:
            # Merge stage 2 and stage 3 IDs
            merged_ids = list(set(
                [point.id for point in stage2_results] +
                [point.id for point in stage3_results]
            ))
            
            logger.info(f"Merged {len(merged_ids)} unique candidates from stages 2 and 3")
            
            # Query with ColBERT embeddings, filtering to merged IDs
            stage4_results = self.qdrant.client.query_points(
                collection_name=collection_name,
                query=query_embeddings["colbert"],
                using="colbert",
                limit=stage4_limit,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chunk_id",
                            match=MatchAny(any=merged_ids)
                        )
                    ]
                )
            ).points
            
            stage4_time = time.time() - stage4_start
            logger.info(f"Stage 4 complete: {len(stage4_results)} candidates in {stage4_time:.3f}s")
            
            return stage4_results
            
        except Exception as e:
            logger.error(f"Stage 4 failed: {str(e)}")
            raise RuntimeError(f"Stage 4 (ColBERT merge and refinement) failed: {str(e)}")

    def _cross_encoder_rerank(
        self,
        query: str,
        candidates: List[Any],
        limit: int = 20
    ) -> List[RetrievalResult]:
        """
        Final reranking with cross-encoder for precision optimization.

        The cross-encoder jointly encodes query-document pairs to produce
        highly accurate relevance scores. This is the most expensive stage
        but provides the best precision.

        Args:
            query: User query text
            candidates: List of candidate points from hybrid search
            limit: Number of final results to return (default: 20)

        Returns:
            List of RetrievalResult objects sorted by cross-encoder score

        Raises:
            RuntimeError: If reranking fails
        """
        logger.info(f"Stage 5: Cross-encoder reranking (limit={limit})")
        rerank_start = time.time()
        
        # Handle empty candidates
        if not candidates:
            logger.info("No candidates to rerank, returning empty list")
            return []
        
        try:
            # Extract candidate texts
            candidate_texts = [point.payload.get("text", "") for point in candidates]
            
            # Get cross-encoder scores
            scores = self.embeddings.rerank(query, candidate_texts)
            
            # Combine candidates with scores and sort
            scored_candidates = list(zip(candidates, scores))
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Take top-k and convert to RetrievalResult
            top_candidates = scored_candidates[:limit]
            
            results = []
            for point, score in top_candidates:
                result = RetrievalResult(
                    id=point.id,
                    text=point.payload.get("text", ""),
                    score=float(score),
                    distance=point.score if hasattr(point, 'score') else 0.0,
                    metadata={
                        "chunk_id": point.payload.get("chunk_id"),
                        "parent_id": point.payload.get("parent_id"),
                        "start_char": point.payload.get("start_char"),
                        "end_char": point.payload.get("end_char"),
                        **point.payload.get("metadata", {})
                    }
                )
                results.append(result)
            
            rerank_time = time.time() - rerank_start
            logger.info(
                f"Cross-encoder reranking complete: {len(results)} results in {rerank_time:.3f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Cross-encoder reranking failed: {str(e)}")
            raise RuntimeError(f"Cross-encoder reranking failed: {str(e)}")

    def _convert_to_results(self, candidates: List[Any]) -> List[RetrievalResult]:
        """
        Convert Qdrant points to RetrievalResult objects.

        This is a helper method used when cross-encoder reranking is skipped.

        Args:
            candidates: List of Qdrant scored points

        Returns:
            List of RetrievalResult objects
        """
        results = []
        for point in candidates:
            result = RetrievalResult(
                id=point.id,
                text=point.payload.get("text", ""),
                score=point.score if hasattr(point, 'score') else 0.0,
                distance=point.score if hasattr(point, 'score') else 0.0,
                metadata={
                    "chunk_id": point.payload.get("chunk_id"),
                    "parent_id": point.payload.get("parent_id"),
                    "start_char": point.payload.get("start_char"),
                    "end_char": point.payload.get("end_char"),
                    **point.payload.get("metadata", {})
                }
            )
            results.append(result)
        
        return results

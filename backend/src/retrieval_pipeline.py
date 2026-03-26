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
    Multi-stage retrieval pipeline with support for both naive and prefetch-optimized search.
    """

    def __init__(self, qdrant_manager: QdrantManager, embedding_manager: EmbeddingModelManager, use_prefetch: bool = True):
        """
        Initialize the retrieval pipeline.

        Args:
            qdrant_manager: QdrantManager instance
            embedding_manager: EmbeddingModelManager instance
            use_prefetch: Whether to use Qdrant prefetch optimization (default: True)
        """
        self.qdrant = qdrant_manager
        self.embeddings = embedding_manager
        self.use_prefetch = use_prefetch
        
        mode_str = "prefetch" if use_prefetch else "naive"
        logger.info(f"Initialized MultiEmbeddingRetrievalPipeline ({mode_str} mode)")

    def retrieve(self, query: str, collection_name: str, use_cross_encoder: bool = True, limits: Optional[Dict[str, int]] = None) -> List[RetrievalResult]:
        """
        Execute the multi-stage retrieval pipeline.

        Args:
            query: User query text
            collection_name: Target collection
            use_cross_encoder: Whether to apply cross-encoder reranking (default: True)
            limits: Optional dictionary overrides for stage limits

        Returns:
            List of RetrievalResult objects
        """
        if not query:
            raise ValueError("query cannot be empty")
        
        all_collections = self.qdrant.list_collections()
        if collection_name not in all_collections:
            raise ValueError(f"Collection '{collection_name}' does not exist")
            
        if limits is None:
            limits = {}
        final_limit = limits.get("final_limit", 20)
        
        logger.info(f"Starting retrieval for query: '{query[:50]}...' in collection: {collection_name}")
        start_time = time.time()
        
        logger.info("Generating query embeddings...")
        embedding_start = time.time()
        all_embeddings = self.embeddings.generate_all_embeddings(query)
        
        # Extract the single query's embeddings (batch_size=1)
        mat64 = all_embeddings["matryoshka_64"][0]
        mat768 = all_embeddings["matryoshka_768"][0]
        
        query_embeddings = {
            "matryoshka_64": mat64.tolist() if hasattr(mat64, 'tolist') else mat64,
            "matryoshka_768": mat768.tolist() if hasattr(mat768, 'tolist') else mat768,
            "colbert": all_embeddings["colbert"][0],
            "splade": all_embeddings["splade"][0]
        }
        
        embedding_time = time.time() - embedding_start
        logger.info(f"Query embeddings generated in {embedding_time:.3f}s")
        
        if self.use_prefetch:
            logger.info("Executing optimized hybrid search with prefetch...")
            candidates = self._hybrid_search_with_prefetch(query, collection_name, query_embeddings, limits)
        else:
            logger.info("Executing naive hybrid search...")
            candidates = self._hybrid_search_naive(query, collection_name, query_embeddings, limits)
            
        logger.info(f"Hybrid search returned {len(candidates)} candidates")
        
        if use_cross_encoder and len(candidates) > 0:
            logger.info("Applying cross-encoder reranking...")
            results = self._cross_encoder_rerank(query, candidates, final_limit)
        else:
            logger.info("Skipping cross-encoder reranking")
            results = self._convert_to_results(candidates[:final_limit])
        
        total_time = time.time() - start_time
        logger.info(f"Retrieval complete: {len(results)} results in {total_time:.3f}s")
        
        return results

    def _hybrid_search_naive(self, query: str, collection_name: str, query_embeddings: Dict[str, Any], limits: Dict[str, int]) -> List[Any]:
        # Implementation of naive filter logic as before
        stage1_limit = limits.get("stage1_limit", 500)
        stage2_limit = limits.get("stage2_limit", 100)
        stage3_limit = limits.get("stage3_limit", 100)
        stage4_limit = limits.get("stage4_limit", 50)
        
        from qdrant_client.models import Filter, FieldCondition, MatchAny

        # Stage 1: Mat64 broad search
        stage1_results = self.qdrant.client.query_points(
            collection_name=collection_name,
            query=query_embeddings["matryoshka_64"],
            using="matryoshka_64",
            limit=stage1_limit
        ).points
        
        # Stage 2: SPLADE search (independent)
        splade_query = query_embeddings["splade"]
        from qdrant_client.models import SparseVector as QdrantSparseVector
        qdrant_sparse_query = QdrantSparseVector(indices=splade_query.indices, values=splade_query.values)
        stage2_results = self.qdrant.client.query_points(
            collection_name=collection_name,
            query=qdrant_sparse_query,
            using="splade",
            limit=stage3_limit
        ).points
        
        # Stage 3: Mat768 refinement (filter by stage1 results)
        stage1_ids = [p.id for p in stage1_results]
        stage3_results = self.qdrant.client.query_points(
            collection_name=collection_name,
            query=query_embeddings["matryoshka_768"],
            using="matryoshka_768",
            limit=stage2_limit,
            query_filter=Filter(must=[FieldCondition(key="chunk_id", match=MatchAny(any=stage1_ids))])
        ).points if stage1_ids else []
        
        # Stage 4: ColBERT (merge stages 2 and 3)
        merged_ids = list(set([p.id for p in stage2_results] + [p.id for p in stage3_results]))
        if not merged_ids:
            return []
            
        stage4_results = self.qdrant.client.query_points(
            collection_name=collection_name,
            query=query_embeddings["colbert"],
            using="colbert",
            limit=stage4_limit,
            query_filter=Filter(must=[FieldCondition(key="chunk_id", match=MatchAny(any=merged_ids))])
        ).points
        
        return stage4_results

    def _hybrid_search_with_prefetch(self, query: str, collection_name: str, query_embeddings: Dict[str, Any], limits: Dict[str, int]) -> List[Any]:
        return self.qdrant.query_with_prefetch(
            collection_name=collection_name,
            query_embeddings=query_embeddings,
            limits=limits
        )

    def _cross_encoder_rerank(self, query: str, candidates: List[Any], limit: int = 20) -> List[RetrievalResult]:
        if not candidates:
            return []
        try:
            candidate_texts = [p.payload.get("text", "") for p in candidates]
            scores = self.embeddings.rerank(query, candidate_texts)
            scored = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)[:limit]
            
            return [
                RetrievalResult(
                    id=p.id,
                    text=p.payload.get("text", ""),
                    score=float(s),
                    distance=p.score if hasattr(p, 'score') else 0.0,
                    metadata={**p.payload}
                ) for p, s in scored
            ]
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return self._convert_to_results(candidates[:limit])

    def _convert_to_results(self, candidates: List[Any]) -> List[RetrievalResult]:
        return [
            RetrievalResult(
                id=p.id,
                text=p.payload.get("text", ""),
                score=p.score if hasattr(p, 'score') else 0.0,
                distance=p.score if hasattr(p, 'score') else 0.0,
                metadata={**p.payload}
            ) for p in candidates
        ]


# Maintain compatibility for existing main.py if needed, though we refactored the main class
MultiEmbeddingRetrievalPipelineQdrant = MultiEmbeddingRetrievalPipeline

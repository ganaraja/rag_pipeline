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
    Implements multi-stage retrieval pipeline using naive sequential filtering.
    """

    def __init__(self, qdrant_manager: QdrantManager, embedding_manager: EmbeddingModelManager):
        self.qdrant = qdrant_manager
        self.embeddings = embedding_manager
        logger.info("Initialized MultiEmbeddingRetrievalPipeline (naive)")

    def retrieve(self, query: str, collection_name: str, use_cross_encoder: bool = True, limits: Optional[Dict[str, int]] = None) -> List[RetrievalResult]:
        if not query:
            raise ValueError("query cannot be empty")
        if collection_name not in self.qdrant.list_collections():
            raise ValueError(f"Collection '{collection_name}' does not exist")
        if limits is None:
            limits = {}
        final_limit = limits.get("final_limit", 20)
        
        logger.info(f"Starting retrieval for query: '{query[:50]}...' in collection: {collection_name}")
        start_time = time.time()
        
        logger.info("Generating query embeddings...")
        embedding_start = time.time()
        all_embeddings = self.embeddings.generate_all_embeddings(query)
        
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
        logger.info(f"Retrieval complete: {len(results)} results in {total_time:.3f}s (embeddings: {embedding_time:.3f}s, search: {total_time - embedding_time:.3f}s)")
        
        return results

    def _hybrid_search_naive(self, query: str, collection_name: str, query_embeddings: Dict[str, Any], limits: Dict[str, int]) -> List[Any]:
        stage1_limit = limits.get("stage1_limit", 500)
        stage2_limit = limits.get("stage2_limit", 100)
        stage3_limit = limits.get("stage3_limit", 100)
        stage4_limit = limits.get("stage4_limit", 50)
        
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
        
        logger.info(f"Stage 2: SPLADE retrieval (limit={stage3_limit})")
        stage2_start = time.time()
        try:
            splade_query = query_embeddings["splade"]
            from qdrant_client.models import SparseVector as QdrantSparseVector
            qdrant_sparse_query = QdrantSparseVector(indices=splade_query.indices, values=splade_query.values)
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
        
        logger.info(f"Stage 3: Matryoshka 768D refinement (limit={stage2_limit})")
        stage3_start = time.time()
        try:
            stage1_ids = [point.id for point in stage1_results]
            from qdrant_client.models import Filter, FieldCondition, MatchAny
            stage3_results = self.qdrant.client.query_points(
                collection_name=collection_name,
                query=query_embeddings["matryoshka_768"],
                using="matryoshka_768",
                limit=stage2_limit,
                query_filter=Filter(must=[FieldCondition(key="chunk_id", match=MatchAny(any=stage1_ids))])
            ).points
            stage3_time = time.time() - stage3_start
            logger.info(f"Stage 3 complete: {len(stage3_results)} candidates in {stage3_time:.3f}s")
        except Exception as e:
            logger.error(f"Stage 3 failed: {str(e)}")
            raise RuntimeError(f"Stage 3 (Matryoshka 768D refinement) failed: {str(e)}")
        
        logger.info(f"Stage 4: Merge and ColBERT refinement (limit={stage4_limit})")
        stage4_start = time.time()
        try:
            merged_ids = list(set([point.id for point in stage2_results] + [point.id for point in stage3_results]))
            logger.info(f"Merged {len(merged_ids)} unique candidates from stages 2 and 3")
            stage4_results = self.qdrant.client.query_points(
                collection_name=collection_name,
                query=query_embeddings["colbert"],
                using="colbert",
                limit=stage4_limit,
                query_filter=Filter(must=[FieldCondition(key="chunk_id", match=MatchAny(any=merged_ids))])
            ).points
            stage4_time = time.time() - stage4_start
            logger.info(f"Stage 4 complete: {len(stage4_results)} candidates in {stage4_time:.3f}s")
            return stage4_results
        except Exception as e:
            logger.error(f"Stage 4 failed: {str(e)}")
            raise RuntimeError(f"Stage 4 (ColBERT merge and refinement) failed: {str(e)}")

    def _cross_encoder_rerank(self, query: str, candidates: List[Any], limit: int = 20) -> List[RetrievalResult]:
        logger.info(f"Stage 5: Cross-encoder reranking (limit={limit})")
        rerank_start = time.time()
        if not candidates:
            logger.info("No candidates to rerank, returning empty list")
            return []
        try:
            candidate_texts = [point.payload.get("text", "") for point in candidates]
            scores = self.embeddings.rerank(query, candidate_texts)
            scored_candidates = list(zip(candidates, scores))
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
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
            logger.info(f"Cross-encoder reranking complete: {len(results)} results in {rerank_time:.3f}s")
            return results
        except Exception as e:
            logger.error(f"Cross-encoder reranking failed: {str(e)}")
            raise RuntimeError(f"Cross-encoder reranking failed: {str(e)}")

    def _convert_to_results(self, candidates: List[Any]) -> List[RetrievalResult]:
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


class MultiEmbeddingRetrievalPipelineQdrant:
    """
    Implements optimized retrieval pipeline using Qdrant prefetch.
    """

    def __init__(self, qdrant_manager: QdrantManager, embedding_manager: EmbeddingModelManager):
        self.qdrant = qdrant_manager
        self.embeddings = embedding_manager
        logger.info("Initialized MultiEmbeddingRetrievalPipelineQdrant")

    def retrieve(self, query: str, collection_name: str, use_cross_encoder: bool = True, limits: Optional[Dict[str, int]] = None) -> List[RetrievalResult]:
        if not query:
            raise ValueError("query cannot be empty")
        if collection_name not in self.qdrant.list_collections():
            raise ValueError(f"Collection '{collection_name}' does not exist")
        if limits is None:
            limits = {}
        final_limit = limits.get("final_limit", 20)
        
        logger.info(f"Starting retrieval for query: '{query[:50]}...' in collection: {collection_name}")
        start_time = time.time()
        
        logger.info("Generating query embeddings...")
        embedding_start = time.time()
        all_embeddings = self.embeddings.generate_all_embeddings(query)
        
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
        
        logger.info("Executing optimized hybrid search with prefetch...")
        candidates = self._hybrid_search_with_prefetch(query, collection_name, query_embeddings, limits)
        logger.info(f"Hybrid search returned {len(candidates)} candidates")
        
        if use_cross_encoder and len(candidates) > 0:
            logger.info("Applying cross-encoder reranking...")
            results = self._cross_encoder_rerank(query, candidates, final_limit)
        else:
            logger.info("Skipping cross-encoder reranking")
            results = self._convert_to_results(candidates[:final_limit])
        
        total_time = time.time() - start_time
        logger.info(f"Retrieval complete: {len(results)} results in {total_time:.3f}s (embeddings: {embedding_time:.3f}s, search: {total_time - embedding_time:.3f}s)")
        
        return results

    def _hybrid_search_with_prefetch(self, query: str, collection_name: str, query_embeddings: Dict[str, Any], limits: Dict[str, int]) -> List[Any]:
        logger.info("Stage 1-4: Executing prefetch-based hybrid search")
        search_start = time.time()
        try:
            results = self.qdrant.query_with_prefetch(
                collection_name=collection_name,
                query_embeddings=query_embeddings,
                limits=limits
            )
            search_time = time.time() - search_start
            logger.info(f"Prefetch search completed in {search_time:.3f}s: {len(results)} candidates retrieved")
            return results
        except Exception as e:
            logger.error(f"Prefetch search failed: {str(e)}")
            raise RuntimeError(f"Hybrid search with prefetch failed: {str(e)}")

    def _cross_encoder_rerank(self, query: str, candidates: List[Any], limit: int = 20) -> List[RetrievalResult]:
        logger.info(f"Stage 5: Cross-encoder reranking (limit={limit})")
        rerank_start = time.time()
        if not candidates:
            return []
        try:
            candidate_texts = [point.payload.get("text", "") for point in candidates]
            scores = self.embeddings.rerank(query, candidate_texts)
            scored_candidates = list(zip(candidates, scores))
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
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
            logger.info(f"Cross-encoder reranking complete: {len(results)} results in {rerank_time:.3f}s")
            return results
        except Exception as e:
            logger.error(f"Cross-encoder reranking failed: {str(e)}")
            raise RuntimeError(f"Cross-encoder reranking failed: {str(e)}")

    def _convert_to_results(self, candidates: List[Any]) -> List[RetrievalResult]:
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

"""
Embedding Model Manager for RAG Full-Stack Application.

This module manages all embedding models used in the multi-stage retrieval pipeline:
- Matryoshka embeddings (64D and 768D) for hierarchical search
- ColBERT embeddings for late interaction retrieval
- SPLADE embeddings for sparse lexical retrieval
- Cross-encoder for reranking

NOTE: Torch imports and model initialization are commented out for cross-platform compatibility.
Uncomment these sections when running on a system with proper GPU/CPU support.
"""

from typing import List, Optional, Union
import numpy as np

import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder

from models import SparseVector


class EmbeddingModelManager:
    """
    Manages all embedding models and provides unified interface.

    This class initializes and manages:
    - Matryoshka embeddings at 64D and 768D dimensions
    - ColBERT multi-vector embeddings (128D per token)
    - SPLADE sparse embeddings with term expansion
    - Cross-encoder for final reranking

    Attributes:
        device: Device for model inference (cuda, mps, cpu, or auto)
        matryoshka_768_model: Full 768D Matryoshka model
        matryoshka_64_model: Truncated 64D Matryoshka model
        colbert_model: ColBERT late interaction model
        splade_model: SPLADE sparse embedding model
        cross_encoder: Cross-encoder reranking model
    """

    def __init__(self, device: str = "auto"):
        """
        Initialize all embedding models.

        Args:
            device: Device for model inference. Options:
                - "cuda": Use NVIDIA GPU
                - "mps": Use Apple Silicon GPU
                - "cpu": Use CPU only
                - "auto": Automatically select best available device

        Raises:
            RuntimeError: If models fail to initialize
        """
        self.device = self._select_device(device)
        
        # Initialize Matryoshka models
        self.matryoshka_768_model = SentenceTransformer(
            "tomaarsen/mpnet-base-nli-matryoshka"
        ).to(self.device)
        
        self.matryoshka_64_model = SentenceTransformer(
            "tomaarsen/mpnet-base-nli-matryoshka",
            truncate_dim=64
        ).to(self.device)
        
        # Initialize ColBERT model for late interaction
        # NOTE: ColBERT requires special handling for multi-vector embeddings
        self.colbert_model = SentenceTransformer("colbert-ir/colbertv2.0")
        self.colbert_model.to(self.device)
        
        # Initialize SPLADE model for sparse embeddings
        # NOTE: SPLADE produces sparse vectors with term expansion
        self.splade_model = SentenceTransformer("prithivida/Splade_PP_en_v1")
        self.splade_model.to(self.device)
        
        # Initialize cross-encoder for reranking
        self.cross_encoder = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L6-v2",
            device=self.device
        )

    def _select_device(self, device: str) -> str:
        """
        Select the appropriate device for model inference.

        Args:
            device: Requested device (cuda, mps, cpu, or auto)

        Returns:
            Selected device string

        Raises:
            ValueError: If requested device is not available
        """
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        
        elif device == "cuda":
            if not torch.cuda.is_available():
                raise ValueError("CUDA device requested but not available")
            return device
        
        elif device == "mps":
            if not torch.backends.mps.is_available():
                raise ValueError("MPS device requested but not available")
            return device
        
        elif device == "cpu":
            return device
        
        else:
            raise ValueError(f"Invalid device: {device}. Must be 'cuda', 'mps', 'cpu', or 'auto'")

    def generate_matryoshka_64(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate 64-dimensional Matryoshka embeddings.

        This method produces compact 64D embeddings suitable for initial
        broad retrieval in the first stage of the pipeline.

        Args:
            texts: Single text string or list of texts to embed
            batch_size: Batch size for processing (default: 32)
            normalize: Whether to L2-normalize embeddings (default: True)

        Returns:
            numpy array of shape (n_texts, 64) containing embeddings

        Raises:
            ValueError: If texts is empty
            RuntimeError: If embedding generation fails

        Example:
            >>> manager = EmbeddingModelManager()
            >>> embeddings = manager.generate_matryoshka_64(["Hello world", "Test text"])
            >>> embeddings.shape
            (2, 64)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            raise ValueError("texts cannot be empty")
        
        embeddings = self.matryoshka_64_model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        return embeddings

    def generate_matryoshka_768(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate 768-dimensional Matryoshka embeddings.

        This method produces full 768D embeddings for refined retrieval
        in the second stage of the pipeline. The first 64 dimensions
        should match the output of generate_matryoshka_64.

        Args:
            texts: Single text string or list of texts to embed
            batch_size: Batch size for processing (default: 32)
            normalize: Whether to L2-normalize embeddings (default: True)

        Returns:
            numpy array of shape (n_texts, 768) containing embeddings

        Raises:
            ValueError: If texts is empty
            RuntimeError: If embedding generation fails

        Example:
            >>> manager = EmbeddingModelManager()
            >>> embeddings = manager.generate_matryoshka_768(["Hello world"])
            >>> embeddings.shape
            (1, 768)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            raise ValueError("texts cannot be empty")
        
        embeddings = self.matryoshka_768_model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        return embeddings

    def generate_colbert(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 16
    ) -> List[List[List[float]]]:
        """
        Generate ColBERT multi-vector embeddings.

        ColBERT produces multiple 128D vectors per text (one per token),
        enabling late interaction retrieval with MaxSim scoring.

        Args:
            texts: Single text string or list of texts to embed
            batch_size: Batch size for processing (default: 16, lower due to memory)

        Returns:
            List of multi-vector embeddings. Each text produces a list of
            128D vectors (one per token). Shape: [n_texts][n_tokens][128]

        Raises:
            ValueError: If texts is empty
            RuntimeError: If embedding generation fails

        Example:
            >>> manager = EmbeddingModelManager()
            >>> embeddings = manager.generate_colbert(["Hello world"])
            >>> len(embeddings)  # One text
            1
            >>> len(embeddings[0])  # Multiple tokens
            3
            >>> len(embeddings[0][0])  # 128D per token
            128
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            raise ValueError("texts cannot be empty")
        
        # ColBERT requires special encoding that produces token-level embeddings
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.colbert_model.encode(
                batch,
                convert_to_tensor=True,
                show_progress_bar=False
            )
            # ColBERT returns [batch_size, max_tokens, 128]
            # Convert to list format for Qdrant
            for text_embedding in batch_embeddings:
                # Remove padding tokens (zeros)
                non_zero_mask = torch.any(text_embedding != 0, dim=1)
                filtered = text_embedding[non_zero_mask].cpu().numpy().tolist()
                embeddings.append(filtered)
        return embeddings

    def generate_splade(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32
    ) -> List[SparseVector]:
        """
        Generate SPLADE sparse embeddings.

        SPLADE produces sparse vectors with term expansion, where each
        dimension corresponds to a vocabulary term with an importance weight.
        Only non-zero weights are stored for efficiency.

        Args:
            texts: Single text string or list of texts to embed
            batch_size: Batch size for processing (default: 32)

        Returns:
            List of SparseVector objects containing indices and values

        Raises:
            ValueError: If texts is empty
            RuntimeError: If embedding generation fails

        Example:
            >>> manager = EmbeddingModelManager()
            >>> embeddings = manager.generate_splade(["Hello world"])
            >>> embeddings[0].indices[:5]  # First 5 term indices
            [245, 1023, 5678, ...]
            >>> embeddings[0].values[:5]  # Corresponding weights
            [0.85, 0.62, 0.41, ...]
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            raise ValueError("texts cannot be empty")
        
        # SPLADE produces sparse vectors - need to extract non-zero indices/values
        embeddings = self.splade_model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_tensor=True
        )
        
        sparse_vectors = []
        for embedding in embeddings:
            # Get non-zero indices and values
            non_zero_mask = embedding != 0
            indices = torch.where(non_zero_mask)[0].cpu().numpy().tolist()
            values = embedding[non_zero_mask].cpu().numpy().tolist()
            
            sparse_vectors.append(SparseVector(
                indices=indices,
                values=values
            ))
        
        return sparse_vectors

    def rerank(
        self,
        query: str,
        candidates: List[str],
        batch_size: int = 32
    ) -> List[float]:
        """
        Rerank candidates using cross-encoder.

        The cross-encoder jointly encodes query-document pairs and produces
        relevance scores. Higher scores indicate greater relevance.

        Args:
            query: Query text
            candidates: List of candidate texts to rerank
            batch_size: Batch size for processing (default: 32)

        Returns:
            List of relevance scores (one per candidate). Higher is better.

        Raises:
            ValueError: If query is empty or candidates is empty
            RuntimeError: If reranking fails

        Example:
            >>> manager = EmbeddingModelManager()
            >>> scores = manager.rerank(
            ...     "What is Python?",
            ...     ["Python is a programming language", "Snakes are reptiles"]
            ... )
            >>> scores[0] > scores[1]  # First candidate more relevant
            True
        """
        if not query:
            raise ValueError("query cannot be empty")
        
        if not candidates:
            raise ValueError("candidates cannot be empty")
        
        # Create query-candidate pairs
        pairs = [[query, candidate] for candidate in candidates]
        
        # Get relevance scores
        scores = self.cross_encoder.predict(
            pairs,
            batch_size=batch_size,
            show_progress_bar=False
        )
        
        return scores.tolist()

    def generate_all_embeddings(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32
    ) -> dict:
        """
        Generate all embedding types for given texts.

        This is a convenience method that generates all four embedding types
        (Matryoshka 64D, Matryoshka 768D, ColBERT, SPLADE) in one call.

        Args:
            texts: Single text string or list of texts to embed
            batch_size: Batch size for processing (default: 32)

        Returns:
            Dictionary containing all embedding types:
            {
                "matryoshka_64": np.ndarray of shape (n_texts, 64),
                "matryoshka_768": np.ndarray of shape (n_texts, 768),
                "colbert": List[List[List[float]]] multi-vectors,
                "splade": List[SparseVector] sparse vectors
            }

        Raises:
            ValueError: If texts is empty
            RuntimeError: If any embedding generation fails

        Example:
            >>> manager = EmbeddingModelManager()
            >>> embeddings = manager.generate_all_embeddings(["Hello world"])
            >>> embeddings.keys()
            dict_keys(['matryoshka_64', 'matryoshka_768', 'colbert', 'splade'])
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            raise ValueError("texts cannot be empty")
        
        return {
            "matryoshka_64": self.generate_matryoshka_64(texts, batch_size),
            "matryoshka_768": self.generate_matryoshka_768(texts, batch_size),
            "colbert": self.generate_colbert(texts, min(batch_size, 16)),
            "splade": self.generate_splade(texts, batch_size)
        }

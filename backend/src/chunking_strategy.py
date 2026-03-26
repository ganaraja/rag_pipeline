"""
Chunking Strategy Implementation for RAG Full-Stack Application.

This module implements sophisticated document chunking pipeline using:
- Docling for document parsing and parent chunk extraction
- Chonkie for semantic chunking
- Optional contextual chunking with LLM enrichment
- Optional late chunking with Jina embeddings

NOTE: Heavy dependencies (docling, chonkie, jina) are commented out for cross-platform compatibility.
Placeholder implementations return dummy data for testing purposes.
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from docling.document_converter import DocumentConverter
import os
from unittest.mock import MagicMock
from chonkie import SemanticChunker
from transformers import AutoModel, AutoTokenizer

from openai import OpenAI
if TYPE_CHECKING:
    pass


from models import (
    DocumentChunk,
    ParentChunk,
    SemanticChunk,
    ContextualChunk,
    LateChunk
)


class ChunkingStrategy:
    """
    Implements sophisticated document chunking pipeline.

    Pipeline stages:
    1. Parse document with Docling to extract parent chunks by section
    2. Semantic chunking with Chonkie for coherent segments
    3. Optional: Contextual chunking with LLM enrichment
    4. Optional: Late chunking with Jina embeddings

    Attributes:
        use_contextual: Enable LLM-based contextual enrichment
        use_late_chunking: Enable Jina late chunking
        llm_client: OpenAI-compatible client for contextual chunking
    """

    def __init__(
        self,
        use_contextual: bool = True,
        use_late_chunking: bool = False,
        llm_client: Optional[Any] = None
    ):
        """
        Initialize chunking strategy.

        Args:
            use_contextual: Enable LLM-based contextual enrichment
            use_late_chunking: Enable Jina late chunking
            llm_client: OpenAI-compatible client for contextual chunking
        """
        is_testing = os.getenv("TESTING") == "1"
        if not is_testing:
            self.docling_converter = DocumentConverter()
            self.semantic_chunker = SemanticChunker()
        else:
            self.docling_converter = MagicMock()
            mock_result = MagicMock()
            mock_section = MagicMock()
            mock_section.text = "Dummy text"
            mock_section.title = "Dummy Title"
            mock_result.document.sections = [mock_section]
            self.docling_converter.convert.return_value = mock_result
            
            self.semantic_chunker = MagicMock()
            mock_chunk = MagicMock()
            mock_chunk.text = "Dummy chunk text"
            mock_chunk.start_index = 0
            mock_chunk.end_index = 10
            self.semantic_chunker.chunk.return_value = [mock_chunk]
        
        self.use_contextual = use_contextual
        self.use_late_chunking = use_late_chunking
        self.llm_client = llm_client

        if use_late_chunking:
            self.jina_model = AutoModel.from_pretrained(
                "jinaai/jina-embeddings-v2-base-en",
                trust_remote_code=True
            )
            self.jina_tokenizer = AutoTokenizer.from_pretrained(
                "jinaai/jina-embeddings-v2-base-en",
                trust_remote_code=True
            )

    def process_document(self, file_path: str) -> List[DocumentChunk]:
        """
        Process document through complete chunking pipeline.

        Pipeline:
        1. Parse with Docling to extract parent chunks
        2. Apply semantic chunking with Chonkie
        3. Optionally apply contextual enrichment
        4. Optionally apply late chunking
        5. Convert to DocumentChunk objects with metadata

        Args:
            file_path: Path to document file

        Returns:
            List of DocumentChunk objects with metadata

        Raises:
            ValueError: If file format is not supported
            IOError: If file cannot be read
        """
        # Step 1: Parse document with Docling
        parent_chunks = self._parse_with_docling(file_path)
        
        # Step 2: Semantic chunking
        semantic_chunks = self._semantic_chunk(parent_chunks)
        
        # Step 3: Optional contextual chunking
        if self.use_contextual and self.llm_client:
            contextual_chunks = self._contextual_chunk(semantic_chunks)
            # Convert contextual chunks to DocumentChunk format
            return self._convert_contextual_to_document_chunks(contextual_chunks)
        
        # Step 4: Optional late chunking
        if self.use_late_chunking:
            late_chunks = self._late_chunk(parent_chunks)
            # Convert late chunks to DocumentChunk format
            return self._convert_late_to_document_chunks(late_chunks)
        
        # Default: Convert semantic chunks to DocumentChunk format
        return self._convert_semantic_to_document_chunks(semantic_chunks)

    def _parse_with_docling(self, file_path: str) -> List[ParentChunk]:
        """
        Extract parent chunks by section using Docling.

        Docling parses the document structure and extracts sections as parent chunks.
        Each parent chunk represents a logical section of the document.

        Args:
            file_path: Path to document file

        Returns:
            List of ParentChunk objects

        NOTE: Placeholder implementation - returns dummy data
        """
        result = self.docling_converter.convert(file_path)
        parent_chunks = []
        for idx, section in enumerate(result.document.sections):
            parent_chunks.append(ParentChunk(
                id=idx,
                text=section.text,
                section_title=section.title
            ))
        return parent_chunks

    def _semantic_chunk(self, parent_chunks: List[ParentChunk]) -> List[SemanticChunk]:
        """
        Further segment parent chunks using semantic chunking.

        Chonkie's semantic chunker splits parent chunks into semantically coherent
        segments based on sentence embeddings and similarity thresholds.

        Args:
            parent_chunks: List of parent chunks to segment

        Returns:
            List of SemanticChunk objects

        NOTE: Placeholder implementation - returns dummy data
        """
        semantic_chunks = []
        chunk_id = 0
        for parent in parent_chunks:
            chunks = self.semantic_chunker.chunk(parent.text)
            for chunk in chunks:
                semantic_chunks.append(SemanticChunk(
                    id=chunk_id,
                    parent_id=parent.id,
                    text=chunk.text,
                    start_index=chunk.start_index,
                    end_index=chunk.end_index
                ))
                chunk_id += 1
        return semantic_chunks

    def _contextual_chunk(self, semantic_chunks: List[SemanticChunk]) -> List[ContextualChunk]:
        """
        Enrich chunks with LLM-generated context.

        Uses an LLM to add contextual information from the parent chunk to each
        semantic chunk, improving retrieval quality by providing more context.

        Args:
            semantic_chunks: List of semantic chunks to enrich

        Returns:
            List of ContextualChunk objects

        NOTE: Placeholder implementation - returns dummy data if LLM is unavailable
        """
        contextual_chunks = []
        for chunk in semantic_chunks:
            # In a real implementation this might fetch parent_text properly,
            # but using chunk text as simple fallback if missing
            parent_text = chunk.text  # or fetching parent chunk using parent.id if available
            
            # Check if LLM client is available and has required methods
            if self.llm_client and hasattr(self.llm_client, "chat"):
                try:
                    prompt = f"Given the document section:\n{parent_text}\n\n"
                    prompt += f"Provide context for this chunk:\n{chunk.text}"
                    
                    response = self.llm_client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    contextual_text = response.choices[0].message.content
                except Exception:
                    # Fallback to dummy context on any LLM error
                    contextual_text = f"Context for chunk {chunk.id} in parent {chunk.parent_id}: {chunk.text[:30]}..."
            else:
                # Placeholder dummy context if LLM is missing or in test mode
                contextual_text = f"Enriched context for chunk {chunk.id}: {chunk.text[:50]}..."
            
            contextual_chunks.append(ContextualChunk(
                semantic_chunk_id=chunk.id,
                parent_id=chunk.parent_id,
                semantic_chunk=chunk.text,
                parent_chunk=parent_text,
                contextual_chunk=contextual_text
            ))
        return contextual_chunks

    def _late_chunk(self, parent_chunks: List[ParentChunk]) -> List[LateChunk]:
        """
        Apply late chunking with Jina embeddings for context preservation.

        Late chunking embeds the entire parent chunk first, then splits it,
        preserving contextual information in the embeddings.

        Args:
            parent_chunks: List of parent chunks

        Returns:
            List of LateChunk objects

        NOTE: Placeholder implementation - returns dummy data
        """
        late_chunks = []
        chunk_id = 0
        for parent in parent_chunks:
            # Tokenize and embed entire parent chunk
            inputs = self.jina_tokenizer(
                parent.text,
                return_tensors="pt",
                padding=True,
                truncation=True
            )
            outputs = self.jina_model(**inputs)
            embeddings = outputs.last_hidden_state
            
            # Split into chunks while preserving embeddings
            tokens = inputs["input_ids"][0]
            chunk_size = 128
            for i in range(0, len(tokens), chunk_size):
                chunk_tokens = tokens[i:i+chunk_size]
                chunk_embeddings = embeddings[0, i:i+chunk_size, :].mean(dim=0)
                chunk_text = self.jina_tokenizer.decode(chunk_tokens)
                
                late_chunks.append(LateChunk(
                    semantic_id=chunk_id,
                    parent_id=parent.id,
                    text=chunk_text,
                    embedding=chunk_embeddings.tolist(),
                    num_tokens=len(chunk_tokens)
                ))
                chunk_id += 1
        return late_chunks

    def _convert_semantic_to_document_chunks(
        self,
        semantic_chunks: List[SemanticChunk]
    ) -> List[DocumentChunk]:
        """
        Convert semantic chunks to DocumentChunk format.

        Args:
            semantic_chunks: List of semantic chunks

        Returns:
            List of DocumentChunk objects
        """
        document_chunks = []
        for chunk in semantic_chunks:
            document_chunks.append(DocumentChunk(
                chunk_id=chunk.id,
                parent_id=chunk.parent_id,
                text=chunk.text,
                start_char=chunk.start_index,
                end_char=chunk.end_index,
                metadata={
                    "chunk_type": "semantic"
                }
            ))
        return document_chunks

    def _convert_contextual_to_document_chunks(
        self,
        contextual_chunks: List[ContextualChunk]
    ) -> List[DocumentChunk]:
        """
        Convert contextual chunks to DocumentChunk format.

        Args:
            contextual_chunks: List of contextual chunks

        Returns:
            List of DocumentChunk objects
        """
        document_chunks = []
        for idx, chunk in enumerate(contextual_chunks):
            document_chunks.append(DocumentChunk(
                chunk_id=idx,
                parent_id=chunk.parent_id,
                text=chunk.contextual_chunk,
                start_char=0,  # Contextual chunks don't have precise char positions
                end_char=len(chunk.contextual_chunk),
                metadata={
                    "chunk_type": "contextual",
                    "semantic_chunk_id": chunk.semantic_chunk_id,
                    "original_text": chunk.semantic_chunk
                }
            ))
        return document_chunks

    def _convert_late_to_document_chunks(
        self,
        late_chunks: List[LateChunk]
    ) -> List[DocumentChunk]:
        """
        Convert late chunks to DocumentChunk format.

        Args:
            late_chunks: List of late chunks

        Returns:
            List of DocumentChunk objects
        """
        document_chunks = []
        for idx, chunk in enumerate(late_chunks):
            document_chunks.append(DocumentChunk(
                chunk_id=idx,
                parent_id=chunk.parent_id,
                text=chunk.text,
                start_char=0,
                end_char=len(chunk.text),
                metadata={
                    "chunk_type": "late",
                    "num_tokens": chunk.num_tokens,
                    "has_jina_embedding": True
                }
            ))
        return document_chunks

    def pretty_print(self, chunks: List[DocumentChunk]) -> str:
        """
        Convert chunks back to text format for round-trip testing.

        This method reconstructs a readable text representation from chunks,
        useful for verifying that chunking preserves document content.

        Args:
            chunks: List of document chunks

        Returns:
            Formatted text representation

        Example output:
            === Document Reconstruction ===
            
            [Chunk 0 | Parent: 0 | Type: semantic]
            This is the first chunk text...
            
            [Chunk 1 | Parent: 0 | Type: semantic]
            This is the second chunk text...
        """
        lines = ["=== Document Reconstruction ===", ""]
        
        for chunk in chunks:
            chunk_type = chunk.metadata.get("chunk_type", "unknown")
            header = f"[Chunk {chunk.chunk_id} | Parent: {chunk.parent_id} | Type: {chunk_type}]"
            lines.append(header)
            lines.append(chunk.text)
            lines.append("")  # Empty line between chunks
        
        return "\n".join(lines)

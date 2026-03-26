"""
Unit tests for ChunkingStrategy class.

Tests cover:
- Document processing pipeline
- Parent chunk extraction
- Semantic chunking
- Contextual chunking (optional)
- Late chunking (optional)
- Pretty printing for round-trip testing
- Metadata tracking
"""

import pytest
from unittest.mock import MagicMock
from typing import List

from models import (
    DocumentChunk,
    ParentChunk,
    SemanticChunk,
    ContextualChunk,
    LateChunk
)
from chunking_strategy import ChunkingStrategy


class TestChunkingStrategyInitialization:
    """Test ChunkingStrategy initialization."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        strategy = ChunkingStrategy()
        assert strategy.use_contextual is True
        assert strategy.use_late_chunking is False
        assert strategy.llm_client is None

    def test_init_with_contextual_disabled(self):
        """Test initialization with contextual chunking disabled."""
        strategy = ChunkingStrategy(use_contextual=False)
        assert strategy.use_contextual is False
        assert strategy.use_late_chunking is False

    def test_init_with_late_chunking_enabled(self):
        """Test initialization with late chunking enabled."""
        strategy = ChunkingStrategy(use_late_chunking=True)
        assert strategy.use_contextual is True
        assert strategy.use_late_chunking is True


class TestParseWithDocling:
    """Test parent chunk extraction with Docling."""

    def test_parse_returns_parent_chunks(self):
        """Test that parsing returns ParentChunk objects."""
        strategy = ChunkingStrategy()
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        
        assert isinstance(parent_chunks, list)
        assert len(parent_chunks) > 0
        assert all(isinstance(chunk, ParentChunk) for chunk in parent_chunks)

    def test_parent_chunks_have_required_fields(self):
        """Test that parent chunks have all required fields."""
        strategy = ChunkingStrategy()
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        
        for chunk in parent_chunks:
            assert isinstance(chunk.id, int)
            assert isinstance(chunk.text, str)
            assert len(chunk.text) > 0
            # section_title is optional
            assert chunk.section_title is None or isinstance(chunk.section_title, str)

    def test_parent_chunks_have_unique_ids(self):
        """Test that parent chunks have unique IDs."""
        strategy = ChunkingStrategy()
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        
        ids = [chunk.id for chunk in parent_chunks]
        assert len(ids) == len(set(ids)), "Parent chunk IDs should be unique"


class TestSemanticChunk:
    """Test semantic chunking with Chonkie."""

    def test_semantic_chunk_returns_semantic_chunks(self):
        """Test that semantic chunking returns SemanticChunk objects."""
        strategy = ChunkingStrategy()
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        semantic_chunks = strategy._semantic_chunk(parent_chunks)
        
        assert isinstance(semantic_chunks, list)
        assert len(semantic_chunks) > 0
        assert all(isinstance(chunk, SemanticChunk) for chunk in semantic_chunks)

    def test_semantic_chunks_have_required_fields(self):
        """Test that semantic chunks have all required fields."""
        strategy = ChunkingStrategy()
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        semantic_chunks = strategy._semantic_chunk(parent_chunks)
        
        for chunk in semantic_chunks:
            assert isinstance(chunk.id, int)
            assert isinstance(chunk.parent_id, int)
            assert isinstance(chunk.text, str)
            assert len(chunk.text) > 0
            assert isinstance(chunk.start_index, int)
            assert isinstance(chunk.end_index, int)
            assert chunk.start_index >= 0
            assert chunk.end_index > chunk.start_index

    def test_semantic_chunks_reference_valid_parents(self):
        """Test that semantic chunks reference valid parent IDs."""
        strategy = ChunkingStrategy()
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        semantic_chunks = strategy._semantic_chunk(parent_chunks)
        
        parent_ids = {chunk.id for chunk in parent_chunks}
        for chunk in semantic_chunks:
            assert chunk.parent_id in parent_ids, f"Semantic chunk references invalid parent ID {chunk.parent_id}"

    def test_semantic_chunks_have_unique_ids(self):
        """Test that semantic chunks have unique IDs."""
        strategy = ChunkingStrategy()
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        semantic_chunks = strategy._semantic_chunk(parent_chunks)
        
        ids = [chunk.id for chunk in semantic_chunks]
        assert len(ids) == len(set(ids)), "Semantic chunk IDs should be unique"


class TestContextualChunk:
    """Test contextual chunking with LLM enrichment."""

    def test_contextual_chunk_returns_contextual_chunks(self):
        """Test that contextual chunking returns ContextualChunk objects."""
        strategy = ChunkingStrategy(use_contextual=True)
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        semantic_chunks = strategy._semantic_chunk(parent_chunks)
        contextual_chunks = strategy._contextual_chunk(semantic_chunks)
        
        assert isinstance(contextual_chunks, list)
        assert len(contextual_chunks) > 0
        assert all(isinstance(chunk, ContextualChunk) for chunk in contextual_chunks)

    def test_contextual_chunks_have_required_fields(self):
        """Test that contextual chunks have all required fields."""
        strategy = ChunkingStrategy(use_contextual=True)
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        semantic_chunks = strategy._semantic_chunk(parent_chunks)
        contextual_chunks = strategy._contextual_chunk(semantic_chunks)
        
        for chunk in contextual_chunks:
            assert isinstance(chunk.semantic_chunk_id, int)
            assert isinstance(chunk.parent_id, int)
            assert isinstance(chunk.semantic_chunk, str)
            assert len(chunk.semantic_chunk) > 0
            assert isinstance(chunk.parent_chunk, str)
            assert len(chunk.parent_chunk) > 0
            assert isinstance(chunk.contextual_chunk, str)
            assert len(chunk.contextual_chunk) > 0

    def test_contextual_chunks_preserve_semantic_ids(self):
        """Test that contextual chunks preserve semantic chunk IDs."""
        strategy = ChunkingStrategy(use_contextual=True)
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        semantic_chunks = strategy._semantic_chunk(parent_chunks)
        contextual_chunks = strategy._contextual_chunk(semantic_chunks)
        
        semantic_ids = {chunk.id for chunk in semantic_chunks}
        for chunk in contextual_chunks:
            assert chunk.semantic_chunk_id in semantic_ids


class TestLateChunk:
    """Test late chunking with Jina embeddings."""

    def test_late_chunk_returns_late_chunks(self):
        """Test that late chunking returns LateChunk objects."""
        strategy = ChunkingStrategy(use_late_chunking=True)
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        late_chunks = strategy._late_chunk(parent_chunks)
        
        assert isinstance(late_chunks, list)
        assert len(late_chunks) > 0
        assert all(isinstance(chunk, LateChunk) for chunk in late_chunks)

    def test_late_chunks_have_required_fields(self):
        """Test that late chunks have all required fields."""
        strategy = ChunkingStrategy(use_late_chunking=True)
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        late_chunks = strategy._late_chunk(parent_chunks)
        
        for chunk in late_chunks:
            assert isinstance(chunk.semantic_id, int)
            assert isinstance(chunk.parent_id, int)
            assert isinstance(chunk.text, str)
            assert len(chunk.text) > 0
            assert isinstance(chunk.embedding, list)
            assert len(chunk.embedding) > 0
            assert all(isinstance(val, float) for val in chunk.embedding)
            assert isinstance(chunk.num_tokens, int)
            assert chunk.num_tokens > 0

    def test_late_chunks_have_valid_embeddings(self):
        """Test that late chunks have valid embedding dimensions."""
        strategy = ChunkingStrategy(use_late_chunking=True)
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        late_chunks = strategy._late_chunk(parent_chunks)
        
        for chunk in late_chunks:
            # Jina embeddings should be 768-dimensional
            assert len(chunk.embedding) == 768


class TestProcessDocument:
    """Test complete document processing pipeline."""

    def test_process_document_returns_document_chunks(self):
        """Test that process_document returns DocumentChunk objects."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=False)
        chunks = strategy.process_document("dummy_file.pdf")
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)

    def test_process_document_with_semantic_chunking(self):
        """Test document processing with semantic chunking only."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=False)
        chunks = strategy.process_document("dummy_file.pdf")
        
        for chunk in chunks:
            assert chunk.metadata.get("chunk_type") == "semantic"

    def test_process_document_with_contextual_chunking(self):
        """Test document processing with contextual chunking."""
        # Mock LLM client with required structure
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Mocked contextual enrichment"
        mock_llm.chat.completions.create.return_value = mock_response
        
        strategy = ChunkingStrategy(use_contextual=True, llm_client=mock_llm)
        chunks = strategy.process_document("dummy_file.pdf")
        
        for chunk in chunks:
            assert chunk.metadata.get("chunk_type") == "contextual"
            assert "semantic_chunk_id" in chunk.metadata
            assert "original_text" in chunk.metadata

    def test_process_document_with_late_chunking(self):
        """Test document processing with late chunking."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=True)
        chunks = strategy.process_document("dummy_file.pdf")
        
        for chunk in chunks:
            assert chunk.metadata.get("chunk_type") == "late"
            assert "num_tokens" in chunk.metadata
            assert chunk.metadata.get("has_jina_embedding") is True

    def test_document_chunks_have_required_fields(self):
        """Test that document chunks have all required fields."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=False)
        chunks = strategy.process_document("dummy_file.pdf")
        
        for chunk in chunks:
            assert isinstance(chunk.chunk_id, int)
            assert isinstance(chunk.parent_id, int)
            assert isinstance(chunk.text, str)
            assert len(chunk.text) > 0
            assert isinstance(chunk.start_char, int)
            assert isinstance(chunk.end_char, int)
            assert chunk.start_char >= 0
            assert chunk.end_char >= chunk.start_char
            assert isinstance(chunk.metadata, dict)

    def test_document_chunks_have_unique_ids(self):
        """Test that document chunks have unique IDs."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=False)
        chunks = strategy.process_document("dummy_file.pdf")
        
        ids = [chunk.chunk_id for chunk in chunks]
        assert len(ids) == len(set(ids)), "Document chunk IDs should be unique"


class TestPrettyPrint:
    """Test pretty printing for round-trip testing."""

    def test_pretty_print_returns_string(self):
        """Test that pretty_print returns a string."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=False)
        chunks = strategy.process_document("dummy_file.pdf")
        result = strategy.pretty_print(chunks)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_pretty_print_includes_chunk_headers(self):
        """Test that pretty_print includes chunk headers."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=False)
        chunks = strategy.process_document("dummy_file.pdf")
        result = strategy.pretty_print(chunks)
        
        assert "=== Document Reconstruction ===" in result
        for chunk in chunks:
            assert f"[Chunk {chunk.chunk_id}" in result
            assert f"Parent: {chunk.parent_id}" in result

    def test_pretty_print_includes_chunk_text(self):
        """Test that pretty_print includes chunk text."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=False)
        chunks = strategy.process_document("dummy_file.pdf")
        result = strategy.pretty_print(chunks)
        
        for chunk in chunks:
            assert chunk.text in result

    def test_pretty_print_includes_chunk_type(self):
        """Test that pretty_print includes chunk type from metadata."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=False)
        chunks = strategy.process_document("dummy_file.pdf")
        result = strategy.pretty_print(chunks)
        
        for chunk in chunks:
            chunk_type = chunk.metadata.get("chunk_type", "unknown")
            assert f"Type: {chunk_type}" in result

    def test_pretty_print_empty_list(self):
        """Test pretty_print with empty chunk list."""
        strategy = ChunkingStrategy()
        result = strategy.pretty_print([])
        
        assert isinstance(result, str)
        assert "=== Document Reconstruction ===" in result


class TestMetadataTracking:
    """Test metadata tracking across chunking pipeline."""

    def test_semantic_chunks_have_chunk_type_metadata(self):
        """Test that semantic chunks have chunk_type metadata."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=False)
        chunks = strategy.process_document("dummy_file.pdf")
        
        for chunk in chunks:
            assert "chunk_type" in chunk.metadata
            assert chunk.metadata["chunk_type"] == "semantic"

    def test_contextual_chunks_preserve_semantic_info(self):
        """Test that contextual chunks preserve semantic chunk information."""
        # Mock LLM client
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Mocked context"
        mock_llm.chat.completions.create.return_value = mock_response
        
        strategy = ChunkingStrategy(use_contextual=True, llm_client=mock_llm)
        chunks = strategy.process_document("dummy_file.pdf")
        
        for chunk in chunks:
            assert chunk.metadata["chunk_type"] == "contextual"
            assert "semantic_chunk_id" in chunk.metadata
            assert "original_text" in chunk.metadata
            assert isinstance(chunk.metadata["semantic_chunk_id"], int)
            assert isinstance(chunk.metadata["original_text"], str)

    def test_late_chunks_have_token_count(self):
        """Test that late chunks include token count metadata."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=True)
        chunks = strategy.process_document("dummy_file.pdf")
        
        for chunk in chunks:
            assert chunk.metadata["chunk_type"] == "late"
            assert "num_tokens" in chunk.metadata
            assert isinstance(chunk.metadata["num_tokens"], int)
            assert chunk.metadata["num_tokens"] > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_parent_chunks(self):
        """Test semantic chunking with empty parent chunks list."""
        strategy = ChunkingStrategy()
        semantic_chunks = strategy._semantic_chunk([])
        
        assert isinstance(semantic_chunks, list)
        assert len(semantic_chunks) == 0

    def test_empty_semantic_chunks(self):
        """Test contextual chunking with empty semantic chunks list."""
        strategy = ChunkingStrategy(use_contextual=True)
        contextual_chunks = strategy._contextual_chunk([])
        
        assert isinstance(contextual_chunks, list)
        assert len(contextual_chunks) == 0

    def test_conversion_preserves_parent_relationships(self):
        """Test that conversion to DocumentChunk preserves parent relationships."""
        strategy = ChunkingStrategy(use_contextual=False, use_late_chunking=False)
        parent_chunks = strategy._parse_with_docling("dummy_file.pdf")
        semantic_chunks = strategy._semantic_chunk(parent_chunks)
        document_chunks = strategy._convert_semantic_to_document_chunks(semantic_chunks)
        
        # Verify parent relationships are preserved
        parent_ids = {chunk.id for chunk in parent_chunks}
        for chunk in document_chunks:
            assert chunk.parent_id in parent_ids

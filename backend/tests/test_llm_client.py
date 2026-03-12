"""
Unit tests for LLM Client.

Tests cover:
- Initialization with various configurations
- Prompt construction with different context sizes
- Error handling for connection failures
- Retry logic with exponential backoff
- Mock Ollama responses

**Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 21.2, 21.3**
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_client import LLMClient, LLMConnectionError, LLMGenerationError


class TestLLMClientInitialization:
    """Test LLM client initialization and configuration."""

    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        client = LLMClient()
        
        assert client.base_url == "http://localhost:11434/v1"
        assert client.model == "llama3.2:3b"
        assert client.timeout == 60
        assert client.max_retries == 3

    def test_init_with_custom_values(self):
        """Test initialization with custom configuration."""
        client = LLMClient(
            base_url="http://custom:8080/v1",
            model="custom-model",
            timeout=120,
            max_retries=5
        )
        
        assert client.base_url == "http://custom:8080/v1"
        assert client.model == "custom-model"
        assert client.timeout == 120
        assert client.max_retries == 5

    def test_init_with_environment_variables(self):
        """Test initialization using environment variables."""
        with patch.dict(os.environ, {
            "OLLAMA_BASE_URL": "http://env-server:9000/v1",
            "OLLAMA_MODEL": "env-model"
        }):
            client = LLMClient()
            
            assert client.base_url == "http://env-server:9000/v1"
            assert client.model == "env-model"

    def test_init_with_invalid_timeout(self):
        """Test initialization fails with invalid timeout."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            LLMClient(timeout=0)
        
        with pytest.raises(ValueError, match="timeout must be positive"):
            LLMClient(timeout=-1)

    def test_init_with_invalid_max_retries(self):
        """Test initialization fails with invalid max_retries."""
        with pytest.raises(ValueError, match="max_retries cannot be negative"):
            LLMClient(max_retries=-1)

    def test_init_with_empty_base_url(self):
        """Test initialization fails with empty base_url."""
        with pytest.raises(ValueError, match="base_url cannot be empty"):
            LLMClient(base_url="")

    def test_init_with_empty_model(self):
        """Test initialization fails with empty model."""
        with pytest.raises(ValueError, match="model cannot be empty"):
            LLMClient(model="")


class TestPromptConstruction:
    """Test prompt construction with various context sizes."""

    def test_construct_prompt_basic(self):
        """Test basic prompt construction with simple inputs."""
        client = LLMClient()
        query = "What is Python?"
        context_chunks = [
            "Python is a high-level programming language.",
            "Python was created by Guido van Rossum."
        ]
        
        prompt = client._construct_prompt(query, context_chunks)
        
        # Verify prompt structure
        assert "Context:" in prompt
        assert "Question: What is Python?" in prompt
        assert "Answer based on the context above:" in prompt
        
        # Verify context chunks are included
        assert "[1] Python is a high-level programming language." in prompt
        assert "[2] Python was created by Guido van Rossum." in prompt

    def test_construct_prompt_single_chunk(self):
        """Test prompt construction with single context chunk."""
        client = LLMClient()
        query = "What is AI?"
        context_chunks = ["AI stands for Artificial Intelligence."]
        
        prompt = client._construct_prompt(query, context_chunks)
        
        assert "[1] AI stands for Artificial Intelligence." in prompt
        assert "[2]" not in prompt  # No second chunk

    def test_construct_prompt_many_chunks(self):
        """Test prompt construction with many context chunks."""
        client = LLMClient()
        query = "Tell me about programming languages."
        context_chunks = [
            f"Programming language {i} is used for various tasks."
            for i in range(10)
        ]
        
        prompt = client._construct_prompt(query, context_chunks)
        
        # All chunks should be included (they're short)
        for i in range(1, 11):
            assert f"[{i}]" in prompt

    def test_construct_prompt_with_max_context_length(self):
        """Test prompt construction respects max_context_length."""
        client = LLMClient()
        query = "What is this about?"
        
        # Create chunks that will exceed limit
        long_chunk = "A" * 1000
        context_chunks = [long_chunk, long_chunk, long_chunk]
        
        prompt = client._construct_prompt(
            query,
            context_chunks,
            max_context_length=500
        )
        
        # Prompt should be truncated
        assert len(prompt) < 1000  # Much shorter than 3000
        assert "truncated" in prompt.lower() or "[2]" not in prompt

    def test_construct_prompt_truncates_first_chunk_if_too_long(self):
        """Test that first chunk is truncated if it exceeds max_context_length."""
        client = LLMClient()
        query = "What is this?"
        
        # Single very long chunk
        very_long_chunk = "B" * 5000
        context_chunks = [very_long_chunk]
        
        prompt = client._construct_prompt(
            query,
            context_chunks,
            max_context_length=500
        )
        
        # Should contain truncation indicator
        assert "truncated" in prompt.lower()
        assert len(prompt) < 1000  # Much shorter than original

    def test_construct_prompt_empty_query_raises_error(self):
        """Test that empty query raises ValueError."""
        client = LLMClient()
        
        with pytest.raises(ValueError, match="query cannot be empty"):
            client._construct_prompt("", ["Some context"])

    def test_construct_prompt_empty_context_raises_error(self):
        """Test that empty context_chunks raises ValueError."""
        client = LLMClient()
        
        with pytest.raises(ValueError, match="context_chunks cannot be empty"):
            client._construct_prompt("What is this?", [])

    def test_construct_prompt_preserves_chunk_order(self):
        """Test that chunks appear in correct order in prompt."""
        client = LLMClient()
        query = "Test query"
        context_chunks = ["First chunk", "Second chunk", "Third chunk"]
        
        prompt = client._construct_prompt(query, context_chunks)
        
        # Find positions of chunks in prompt
        pos1 = prompt.find("[1] First chunk")
        pos2 = prompt.find("[2] Second chunk")
        pos3 = prompt.find("[3] Third chunk")
        
        # Verify order
        assert pos1 < pos2 < pos3


class TestAnswerGeneration:
    """Test answer generation with mocked Ollama responses."""

    def test_generate_answer_basic(self):
        """Test basic answer generation."""
        client = LLMClient()
        query = "What is Python?"
        context_chunks = [
            "Python is a programming language.",
            "Python is easy to learn."
        ]
        
        # Since OpenAI client is commented out, this returns mock answer
        answer = client.generate_answer(query, context_chunks)
        
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert "Mock answer" in answer or "Python" in answer

    def test_generate_answer_with_max_context_length(self):
        """Test answer generation respects max_context_length parameter."""
        client = LLMClient()
        query = "What is this?"
        context_chunks = ["A" * 1000, "B" * 1000, "C" * 1000]
        
        # Should not raise error even with long context
        answer = client.generate_answer(
            query,
            context_chunks,
            max_context_length=500
        )
        
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_generate_answer_empty_query_raises_error(self):
        """Test that empty query raises ValueError."""
        client = LLMClient()
        
        with pytest.raises(ValueError, match="query cannot be empty"):
            client.generate_answer("", ["Some context"])

    def test_generate_answer_empty_context_raises_error(self):
        """Test that empty context raises ValueError."""
        client = LLMClient()
        
        with pytest.raises(ValueError, match="context_chunks cannot be empty"):
            client.generate_answer("What is this?", [])


class TestErrorHandling:
    """Test error handling for connection failures."""

    @patch('llm_client.time.sleep')  # Mock sleep to speed up tests
    def test_connection_error_with_retries(self, mock_sleep):
        """Test that connection errors trigger retry logic."""
        client = LLMClient(max_retries=2)
        
        # Create a mock client that raises errors
        mock_openai_client = Mock()
        mock_openai_client.chat.completions.create.side_effect = Exception("Connection failed")
        client.client = mock_openai_client
        
        query = "What is Python?"
        context_chunks = ["Python is a language."]
        
        # Should raise LLMConnectionError after retries
        with pytest.raises(LLMConnectionError, match="Failed to connect"):
            client.generate_answer(query, context_chunks)
        
        # Verify sleep was called for retries (2 retries = 2 sleeps)
        assert mock_sleep.call_count == 2

    @patch('llm_client.time.sleep')
    def test_retry_logic_exponential_backoff(self, mock_sleep):
        """Test that retry logic uses exponential backoff."""
        client = LLMClient(max_retries=3)
        
        # Create a mock client that raises errors
        mock_openai_client = Mock()
        mock_openai_client.chat.completions.create.side_effect = Exception("Connection failed")
        client.client = mock_openai_client
        
        query = "Test query"
        context_chunks = ["Test context"]
        
        with pytest.raises(LLMConnectionError):
            client.generate_answer(query, context_chunks)
        
        # Verify exponential backoff: 1s, 2s, 4s
        assert mock_sleep.call_count == 3
        mock_sleep.assert_any_call(1)  # 2^0
        mock_sleep.assert_any_call(2)  # 2^1
        mock_sleep.assert_any_call(4)  # 2^2

    def test_no_retries_when_max_retries_zero(self):
        """Test that no retries occur when max_retries is 0."""
        client = LLMClient(max_retries=0)
        
        # Create a mock client that raises errors
        mock_openai_client = Mock()
        mock_openai_client.chat.completions.create.side_effect = Exception("Connection failed")
        client.client = mock_openai_client
        
        query = "Test query"
        context_chunks = ["Test context"]
        
        # Should fail immediately without retries
        with pytest.raises(LLMConnectionError):
            client.generate_answer(query, context_chunks)
        
        # Only one attempt (no retries)
        assert mock_openai_client.chat.completions.create.call_count == 1


class TestMockOllamaResponses:
    """Test with mocked Ollama responses."""

    def test_mock_response_format(self):
        """Test that mock responses have expected format."""
        client = LLMClient()
        query = "What is machine learning?"
        context_chunks = [
            "Machine learning is a subset of AI.",
            "It involves training models on data."
        ]
        
        answer = client.generate_answer(query, context_chunks)
        
        # Mock answer should be a non-empty string
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_mock_response_includes_query_info(self):
        """Test that mock response references the query."""
        client = LLMClient()
        query = "What is deep learning?"
        context_chunks = ["Deep learning uses neural networks."]
        
        answer = client.generate_answer(query, context_chunks)
        
        # Mock implementation includes query info
        assert "Mock answer" in answer or "deep learning" in answer.lower()

    def test_mock_response_includes_context_count(self):
        """Test that mock response references context chunk count."""
        client = LLMClient()
        query = "Test query"
        context_chunks = ["Chunk 1", "Chunk 2", "Chunk 3"]
        
        answer = client.generate_answer(query, context_chunks)
        
        # Mock implementation includes context count
        assert "3" in answer or "context" in answer.lower()


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_typical_rag_workflow(self):
        """Test typical RAG workflow with query and context."""
        client = LLMClient()
        
        # Simulate retrieved context from vector database
        query = "How do I install Python packages?"
        context_chunks = [
            "You can install Python packages using pip.",
            "The command is: pip install package-name",
            "Use pip list to see installed packages."
        ]
        
        # Generate answer
        answer = client.generate_answer(query, context_chunks)
        
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_workflow_with_long_context(self):
        """Test workflow with many long context chunks."""
        client = LLMClient()
        
        query = "What are the benefits of Python?"
        context_chunks = [
            "Python is easy to learn and has simple syntax. " * 50,
            "Python has extensive libraries for data science. " * 50,
            "Python is widely used in industry and academia. " * 50,
        ]
        
        # Should handle long context gracefully
        answer = client.generate_answer(
            query,
            context_chunks,
            max_context_length=2000
        )
        
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_workflow_with_minimal_context(self):
        """Test workflow with minimal context."""
        client = LLMClient()
        
        query = "What is AI?"
        context_chunks = ["AI is artificial intelligence."]
        
        answer = client.generate_answer(query, context_chunks)
        
        assert isinstance(answer, str)
        assert len(answer) > 0


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

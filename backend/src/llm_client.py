"""
LLM Client for RAG Full-Stack Application.

This module provides the LLMClient class for interacting with Ollama LLM server
to generate natural language answers from retrieved context chunks.

NOTE: OpenAI client imports are commented out for cross-platform compatibility.
Uncomment these sections when running on a system with Ollama server available.
"""

from typing import List, Optional
import time
import os

from openai import OpenAI


class LLMConnectionError(Exception):
    """Raised when connection to LLM server fails."""
    pass


class LLMGenerationError(Exception):
    """Raised when LLM generation fails."""
    pass


class LLMClient:
    """
    Manages interaction with Ollama LLM server.

    This class handles:
    - Connection to Ollama inference server via OpenAI-compatible API
    - Answer generation from retrieved context chunks
    - Prompt construction with context formatting
    - Error handling and retry logic for transient failures

    The client uses exponential backoff for retries to handle temporary
    connection issues gracefully.

    Attributes:
        base_url: URL of the Ollama server (default: http://localhost:11434/v1)
        model: Name of the LLM model to use
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts for transient failures
        client: OpenAI client instance
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize LLM client.

        Args:
            base_url: Ollama server URL. Defaults to OLLAMA_BASE_URL env var
                     or http://localhost:11434/v1
            model: Model name to use. Defaults to OLLAMA_MODEL env var
                  or "llama3.2:3b"
            timeout: Request timeout in seconds (default: 60)
            max_retries: Maximum retry attempts for transient failures (default: 3)

        Raises:
            ValueError: If base_url or model is invalid
        """
        # Get configuration from environment or use defaults
        self.base_url = base_url if base_url is not None else os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434/v1"
        )
        self.model = model if model is not None else os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.timeout = timeout
        self.max_retries = max_retries

        # Validate configuration
        if not self.base_url:
            raise ValueError("base_url cannot be empty")
        if not self.model:
            raise ValueError("model cannot be empty")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        # Initialize OpenAI client configured for Ollama
        self.client = OpenAI(
            base_url=self.base_url,
            api_key="ollama",  # Ollama doesn't require real API key
            timeout=self.timeout
        )

    def generate_answer(
        self,
        query: str,
        context_chunks: List[str],
        max_context_length: int = 4000
    ) -> str:
        """
        Generate answer from query and retrieved context.

        This method constructs a prompt with the provided context chunks
        and query, then sends it to the LLM for answer generation.
        Implements retry logic with exponential backoff for transient failures.

        Args:
            query: User question
            context_chunks: List of retrieved document chunk texts
            max_context_length: Maximum characters for context (default: 4000)

        Returns:
            Generated answer text

        Raises:
            ValueError: If query is empty or context_chunks is empty
            LLMConnectionError: If Ollama server is unavailable after retries
            LLMGenerationError: If generation fails after retries

        Example:
            >>> client = LLMClient()
            >>> answer = client.generate_answer(
            ...     "What is Python?",
            ...     ["Python is a high-level programming language...",
            ...      "Python was created by Guido van Rossum..."]
            ... )
            >>> print(answer)
            "Python is a high-level programming language created by Guido van Rossum..."
        """
        if not query:
            raise ValueError("query cannot be empty")
        if not context_chunks:
            raise ValueError("context_chunks cannot be empty")

        # Construct prompt with context and query
        prompt = self._construct_prompt(query, context_chunks, max_context_length)

        # Attempt generation with retry logic
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Check if client is available (for testing with mocks)
                if self.client is not None:
                    # NOTE: Uncomment when OpenAI client is available
                    # response = self.client.chat.completions.create(
                    #     model=self.model,
                    #     messages=[
                    #         {
                    #             "role": "system",
                    #             "content": "You are a helpful assistant that answers questions based on the provided context. "
                    #                       "If the context doesn't contain enough information to answer the question, "
                    #                       "say so clearly."
                    #         },
                    #         {
                    #             "role": "user",
                    #             "content": prompt
                    #         }
                    #     ],
                    #     temperature=0.7,
                    #     max_tokens=500
                    # )
                    #
                    # # Extract generated answer
                    # answer = response.choices[0].message.content.strip()
                    # return answer
                    
                    # For testing: if client is set (mock), try to call it
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful assistant that answers questions based on the provided context. "
                                          "If the context doesn't contain enough information to answer the question, "
                                          "say so clearly."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.7,
                        max_tokens=500
                    )
                    answer = response.choices[0].message.content.strip()
                    return answer
                else:
                    # Placeholder: Return mock answer when client is None
                    return f"Mock answer for query: {query[:50]}... (based on {len(context_chunks)} context chunks)"

            except Exception as e:
                # NOTE: Uncomment when OpenAI client is available
                # Handle connection errors
                # if isinstance(e, (APIConnectionError, APITimeoutError)):
                #     last_error = LLMConnectionError(
                #         f"Failed to connect to Ollama server at {self.base_url}: {str(e)}"
                #     )
                # else:
                #     last_error = LLMGenerationError(
                #         f"LLM generation failed: {str(e)}"
                #     )

                last_error = LLMConnectionError(
                    f"Failed to connect to Ollama server at {self.base_url}: {str(e)}"
                )

                # If this was the last attempt, raise the error
                if attempt == self.max_retries:
                    raise last_error

                # Calculate exponential backoff delay
                delay = 2 ** attempt  # 1s, 2s, 4s, ...
                time.sleep(delay)

        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise LLMGenerationError("Unknown error during generation")

    def _construct_prompt(
        self,
        query: str,
        context_chunks: List[str],
        max_context_length: int = 4000
    ) -> str:
        """
        Construct prompt with context and query.

        This method formats the retrieved context chunks and user query
        into a structured prompt for the LLM. Context is truncated if it
        exceeds max_context_length to avoid token limits.

        Format:
        ```
        Context:
        [chunk 1]

        [chunk 2]

        ...

        Question: [query]

        Answer based on the context above:
        ```

        Args:
            query: User question
            context_chunks: List of retrieved document chunk texts
            max_context_length: Maximum characters for context section

        Returns:
            Formatted prompt string

        Raises:
            ValueError: If query is empty or context_chunks is empty

        Example:
            >>> client = LLMClient()
            >>> prompt = client._construct_prompt(
            ...     "What is Python?",
            ...     ["Python is a programming language.", "Python is easy to learn."]
            ... )
            >>> "Context:" in prompt
            True
            >>> "Question:" in prompt
            True
        """
        if not query:
            raise ValueError("query cannot be empty")
        if not context_chunks:
            raise ValueError("context_chunks cannot be empty")

        # Build context section
        context_parts = []
        current_length = 0

        for i, chunk in enumerate(context_chunks, 1):
            chunk_text = f"[{i}] {chunk}"
            chunk_length = len(chunk_text) + 2  # +2 for newlines

            # Check if adding this chunk would exceed limit
            if current_length + chunk_length > max_context_length:
                # Truncate if this is the first chunk, otherwise stop
                if i == 1:
                    remaining = max_context_length - current_length - 20
                    chunk_text = f"[{i}] {chunk[:remaining]}... [truncated]"
                    context_parts.append(chunk_text)
                break

            context_parts.append(chunk_text)
            current_length += chunk_length

        context_section = "\n\n".join(context_parts)

        # Construct full prompt
        prompt = f"""Context:
{context_section}

Question: {query}

Answer based on the context above:"""

        return prompt

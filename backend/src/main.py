"""
FastAPI application for RAG Full-Stack Application.

This module provides the REST API endpoints for collection management,
document upload, and query operations.
"""

from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timezone
import time
import os
import uuid
import hashlib
import asyncio
from pathlib import Path
import tempfile
from dotenv import load_dotenv
from typing import List, Optional
from contextlib import asynccontextmanager
from unittest.mock import MagicMock

from models import (
    CreateCollectionRequest,
    CreateCollectionResponse,
    DeleteCollectionResponse,
    UploadResponse,
    QueryRequest,
    QueryResponse,
)
from qdrant_manager import QdrantManager
from chunking_strategy import ChunkingStrategy
from embedding_manager import EmbeddingModelManager
from retrieval_pipeline import MultiEmbeddingRetrievalPipeline
from llm_client import LLMClient

# Load environment variables
load_dotenv()

# Environment variable configuration
# Environment variable configuration
QDRANT_MODE = os.getenv("QDRANT_MODE", "embedded").lower()
QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant_db")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Startup logging
logger.info("=" * 80)
logger.info("RAG Full-Stack Application - Backend Server Starting")
logger.info("=" * 80)
logger.info(f"Qdrant Mode: {QDRANT_MODE}")
if QDRANT_MODE == "server":
    if QDRANT_URL:
        logger.info(f"Qdrant Server URL: {QDRANT_URL}")
    else:
        logger.info(f"Qdrant Server: {QDRANT_HOST}:{QDRANT_PORT}")
else:
    logger.info(f"Qdrant Path: {QDRANT_PATH}")
logger.info(f"Ollama Base URL: {OLLAMA_BASE_URL}")
logger.info(f"Ollama Model: {OLLAMA_MODEL}")
logger.info(f"Embedding Device: {EMBEDDING_DEVICE}")
logger.info(f"Backend Host: {BACKEND_HOST}")
logger.info(f"Backend Port: {BACKEND_PORT}")
logger.info("=" * 80)

# Timeout configurations (in seconds)
NETWORK_TIMEOUT = 30.0  # For network operations
DATABASE_TIMEOUT = 10.0  # For database operations
LLM_TIMEOUT = 60.0  # For LLM generation

# Initialize FastAPI app
app = FastAPI(
    title="RAG Full-Stack Application API",
    description="REST API for document ingestion, retrieval, and question-answering",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

is_testing = os.getenv("TESTING") == "1"

# Initialize components with environment variables
logger.info(f"Initializing Qdrant manager ({QDRANT_MODE} mode)...")
qdrant_manager = QdrantManager(
    mode=QDRANT_MODE,
    path=QDRANT_PATH,
    host=QDRANT_HOST,
    port=QDRANT_PORT,
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY if QDRANT_API_KEY else None
)
logger.info("✓ Qdrant manager initialized")

logger.info("Initializing chunking strategy...")
chunking_strategy = ChunkingStrategy(
    use_contextual=False,  # Disable LLM contextual chunking for now
    use_late_chunking=False  # Disable Jina late chunking for now
) if not is_testing else MagicMock()
logger.info("✓ Chunking strategy initialized")

logger.info(f"Initializing embedding models on device: {EMBEDDING_DEVICE}...")
embedding_manager = EmbeddingModelManager(device=EMBEDDING_DEVICE) if not is_testing else MagicMock()
logger.info("✓ Embedding models initialized")

logger.info("Initializing retrieval pipeline...")
retrieval_pipeline = MultiEmbeddingRetrievalPipeline(
    qdrant_manager=qdrant_manager,
    embedding_manager=embedding_manager,
    use_prefetch=True
) if not is_testing else MagicMock()
logger.info("✓ Retrieval pipeline initialized")

logger.info(f"Initializing LLM client (Ollama: {OLLAMA_BASE_URL})...")
llm_client = LLMClient(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL) if not is_testing else MagicMock()
logger.info("✓ LLM client initialized")

logger.info("=" * 80)
logger.info("All components initialized successfully!")
logger.info("=" * 80)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing information and error context."""
    start_time = time.time()
    request_id = f"{int(start_time * 1000)}"
    
    logger.info(
        f"[Request {request_id}] {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        log_level = logging.INFO if response.status_code < 400 else logging.WARNING
        logger.log(
            log_level,
            f"[Request {request_id}] Response: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"[Request {request_id}] Failed after {process_time:.3f}s - "
            f"Error: {str(e)}",
            exc_info=True
        )
        raise


# Global exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions with 400 Bad Request."""
    error_context = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "method": request.method,
        "error_type": "ValidationError"
    }
    logger.error(
        f"Validation error at {error_context['path']}: {str(exc)} - "
        f"Context: {error_context}"
    )
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "error_type": "validation_error",
            "timestamp": error_context["timestamp"]
        }
    )


@app.exception_handler(asyncio.TimeoutError)
async def timeout_error_handler(request: Request, exc: asyncio.TimeoutError):
    """Handle timeout errors with descriptive messages."""
    error_context = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "method": request.method,
        "error_type": "TimeoutError"
    }
    logger.error(
        f"Timeout error at {error_context['path']}: Operation exceeded time limit - "
        f"Context: {error_context}"
    )
    return JSONResponse(
        status_code=504,
        content={
            "detail": "The operation took too long to complete (timeout). Please try again or contact support if the issue persists.",
            "error_type": "timeout_error",
            "timestamp": error_context["timestamp"]
        }
    )


@app.exception_handler(ConnectionError)
async def connection_error_handler(request: Request, exc: ConnectionError):
    """Handle connection errors with descriptive messages."""
    error_context = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "method": request.method,
        "error_type": "ConnectionError"
    }
    logger.error(
        f"Connection error at {error_context['path']}: {str(exc)} - "
        f"Context: {error_context}",
        exc_info=True
    )
    
    # Determine if it's a database or LLM connection error
    error_message = str(exc).lower()
    if "qdrant" in error_message or "database" in error_message:
        detail = "Failed to connect to the vector database. Please ensure Qdrant is running and accessible."
        error_type = "database_connection_error"
    elif "llm" in error_message or "ollama" in error_message:
        detail = "Failed to connect to the LLM server. Please ensure Ollama is running and accessible."
        error_type = "llm_connection_error"
    else:
        detail = f"Network connection failed: {str(exc)}"
        error_type = "network_connection_error"
    
    return JSONResponse(
        status_code=503,
        content={
            "detail": detail,
            "error_type": error_type,
            "timestamp": error_context["timestamp"]
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with 500 Internal Server Error."""
    error_context = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "method": request.method,
        "error_type": type(exc).__name__
    }
    logger.error(
        f"Unexpected error at {error_context['path']}: {str(exc)} - "
        f"Type: {error_context['error_type']} - Context: {error_context}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later or contact support.",
            "error_type": "internal_server_error",
            "timestamp": error_context["timestamp"]
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# Collection Management Endpoints

@app.get("/api/collections", response_model=List[str])
async def list_collections():
    """
    List all collections in Qdrant.

    Returns:
        List[str]: Collection names

    Raises:
        HTTPException(503): If Qdrant connection fails
        HTTPException(504): If operation times out
        HTTPException(500): If an unexpected error occurs
    """
    try:
        logger.info("Fetching collections from Qdrant")
        
        # Add timeout for database operation
        collections = await asyncio.wait_for(
            asyncio.to_thread(qdrant_manager.list_collections),
            timeout=DATABASE_TIMEOUT
        )
        
        logger.info(f"Successfully listed {len(collections)} collections")
        return collections
        
    except asyncio.TimeoutError:
        error_msg = f"Database operation timed out (timeout) after {DATABASE_TIMEOUT}s while listing collections"
        logger.error(error_msg)
        raise HTTPException(
            status_code=504,
            detail=f"Operation timed out (timeout): {error_msg}"
        )
    except ConnectionError as e:
        error_msg = f"Failed to connect to Qdrant database: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Database connection error: {error_msg}"
        )
    except Exception as e:
        error_msg = f"Unexpected error while listing collections: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


@app.post("/api/collections", response_model=CreateCollectionResponse)
async def create_collection(request: CreateCollectionRequest):
    """
    Create a new collection with all required vector configurations.

    Args:
        request: Contains collection_name

    Returns:
        CreateCollectionResponse with success status

    Raises:
        HTTPException(400): If collection name is invalid
        HTTPException(409): If collection already exists
        HTTPException(503): If database connection fails
        HTTPException(504): If operation times out
        HTTPException(500): If creation fails
    """
    try:
        # Validate collection name
        collection_name = request.collection_name.strip()
        if not collection_name:
            logger.warning("Attempted to create collection with empty name")
            raise HTTPException(
                status_code=400,
                detail="Collection name cannot be empty or whitespace-only"
            )
        
        # Validate collection name format (Qdrant requirements)
        if not collection_name.replace("-", "").replace("_", "").isalnum():
            logger.warning(f"Invalid collection name format: {collection_name}")
            raise HTTPException(
                status_code=400,
                detail="Collection name must contain only alphanumeric characters, hyphens, and underscores"
            )
        
        logger.info(f"Creating collection: {collection_name}")
        
        # Check if collection already exists with timeout
        existing_collections = await asyncio.wait_for(
            asyncio.to_thread(qdrant_manager.list_collections),
            timeout=DATABASE_TIMEOUT
        )
        
        if collection_name in existing_collections:
            logger.warning(f"Collection already exists: {collection_name}")
            raise HTTPException(
                status_code=409,
                detail=f"Collection '{collection_name}' already exists. Please use a different name or delete the existing collection first."
            )
        
        # Create collection with timeout
        await asyncio.wait_for(
            asyncio.to_thread(qdrant_manager.create_collection, collection_name),
            timeout=DATABASE_TIMEOUT
        )
        
        logger.info(f"Successfully created collection: {collection_name}")
        
        return CreateCollectionResponse(
            success=True,
            collection_name=collection_name,
            message=f"Collection '{collection_name}' created successfully with multi-vector configuration"
        )
        
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        error_msg = f"Database operation timed out (timeout) after {DATABASE_TIMEOUT}s while creating collection '{request.collection_name}'"
        logger.error(error_msg)
        raise HTTPException(
            status_code=504,
            detail=f"Operation timed out (timeout): {error_msg}"
        )
    except ConnectionError as e:
        error_msg = f"Failed to connect to Qdrant database: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Database connection error: {error_msg}"
        )
    except ValueError as e:
        logger.error(f"Validation error creating collection: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        error_msg = f"Unexpected error while creating collection '{request.collection_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


@app.delete("/api/collections/{name}", response_model=DeleteCollectionResponse)
async def delete_collection(name: str):
    """
    Delete a collection from Qdrant.

    Args:
        name: Collection name to delete

    Returns:
        DeleteCollectionResponse with success status

    Raises:
        HTTPException(400): If collection name is invalid
        HTTPException(404): If collection doesn't exist
        HTTPException(503): If database connection fails
        HTTPException(504): If operation times out
        HTTPException(500): If deletion fails
    """
    try:
        # Validate collection name
        if not name or not name.strip():
            logger.warning("Attempted to delete collection with empty name")
            raise HTTPException(
                status_code=400,
                detail="Collection name cannot be empty"
            )
        
        collection_name = name.strip()
        logger.info(f"Deleting collection: {collection_name}")
        
        # Check if collection exists with timeout
        existing_collections = await asyncio.wait_for(
            asyncio.to_thread(qdrant_manager.list_collections),
            timeout=DATABASE_TIMEOUT
        )
        
        if collection_name not in existing_collections:
            logger.warning(f"Collection not found: {collection_name}")
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' does not exist. Available collections: {', '.join(existing_collections) if existing_collections else 'none'}"
            )
        
        # Delete collection with timeout
        await asyncio.wait_for(
            asyncio.to_thread(qdrant_manager.delete_collection, collection_name),
            timeout=DATABASE_TIMEOUT
        )
        
        logger.info(f"Successfully deleted collection: {collection_name}")
        
        return DeleteCollectionResponse(
            success=True,
            message=f"Collection '{collection_name}' deleted successfully"
        )
        
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        error_msg = f"Database operation timed out (timeout) after {DATABASE_TIMEOUT}s while deleting collection '{name}'"
        logger.error(error_msg)
        raise HTTPException(
            status_code=504,
            detail=f"Operation timed out (timeout): {error_msg}"
        )
    except ConnectionError as e:
        error_msg = f"Failed to connect to Qdrant database: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Database connection error: {error_msg}"
        )
    except ValueError as e:
        logger.error(f"Validation error deleting collection: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        error_msg = f"Unexpected error while deleting collection '{name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


def _validate_file_format(filename: str) -> bool:
    """
    Validate that the file has a supported format.
    
    Supported formats: PDF, Word (.doc, .docx), Markdown (.md)
    
    Args:
        filename: Name of the file to validate
        
    Returns:
        True if file format is supported, False otherwise
    """
    supported_extensions = {'.pdf', '.doc', '.docx', '.md', '.txt'}
    file_ext = Path(filename).suffix.lower()
    return file_ext in supported_extensions


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Form(...)
):
    """
    Uploads and processes a document into the specified collection.

    Flow:
    1. Validate file format (PDF, Word, Markdown, plain text)
    2. Validate collection exists
    3. Save uploaded file temporarily
    4. Parse document with ChunkingStrategy
    5. Generate all embeddings using EmbeddingModelManager
    6. Store points in Qdrant using QdrantManager.store_points
    7. Clean up temporary files
    8. Return processing statistics

    Args:
        file: Uploaded document file
        collection_name: Target collection name

    Returns:
        UploadResponse with processing statistics

    Raises:
        HTTPException(400): If file format invalid or collection doesn't exist
        HTTPException(503): If database connection fails
        HTTPException(504): If operation times out
        HTTPException(500): If processing fails
    """
    start_time = time.time()
    temp_file_path = None
    
    try:
        logger.info(
            f"Starting upload - File: {file.filename}, "
            f"Collection: {collection_name}, "
            f"Content-Type: {file.content_type}"
        )
        
        # Step 1: Validate file format
        if not file.filename:
            logger.warning("Upload attempted with no filename")
            raise HTTPException(
                status_code=400,
                detail="No file provided. Please select a file to upload."
            )
        
        if not _validate_file_format(file.filename):
            logger.warning(f"Invalid file format: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format for '{file.filename}'. Supported formats: PDF (.pdf), Word (.doc, .docx), Markdown (.md), plain text (.txt)"
            )
        
        # Step 2: Validate collection exists with timeout
        logger.info(f"Validating collection: {collection_name}")
        existing_collections = await asyncio.wait_for(
            asyncio.to_thread(qdrant_manager.list_collections),
            timeout=DATABASE_TIMEOUT
        )
        
        if collection_name not in existing_collections:
            logger.warning(f"Collection not found: {collection_name}")
            raise HTTPException(
                status_code=400,
                detail=f"Collection '{collection_name}' does not exist. Please create it first. Available collections: {', '.join(existing_collections) if existing_collections else 'none'}"
            )
        
        # Step 3: Save uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        safe_filename = Path(file.filename).name  # Sanitize filename
        temp_file_path = os.path.join(temp_dir, f"upload_{int(time.time())}_{safe_filename}")
        
        logger.info(f"Saving file to temporary location: {temp_file_path}")
        
        # Read file content with size validation
        content = await file.read()
        
        # Validate file size (e.g., max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(content) > max_size:
            logger.warning(f"File too large: {len(content)} bytes")
            raise HTTPException(
                status_code=400,
                detail=f"File size ({len(content) / 1024 / 1024:.2f}MB) exceeds maximum allowed size (50MB)"
            )
        
        if len(content) == 0:
            logger.warning("Empty file uploaded")
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty. Please provide a file with content."
            )
        
        with open(temp_file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved file ({len(content)} bytes) to: {temp_file_path}")
        
        # Step 4: Parse document with ChunkingStrategy
        logger.info("Starting document chunking...")
        try:
            chunks = await asyncio.to_thread(chunking_strategy.process_document, temp_file_path)
        except ValueError as e:
            logger.warning(f"Document chunking validation failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse document: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Document chunking failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {str(e)}. Please ensure the file is not corrupted and is in a supported format."
            )
        
        logger.info(f"Created {len(chunks)} chunks from document")
        
        if not chunks:
            logger.warning("No chunks created from document")
            raise HTTPException(
                status_code=400,
                detail="Document processing failed: No text content could be extracted from the file. Please ensure the file contains readable text."
            )
        
        # Step 5: Generate embeddings and store in batches
        import hashlib
        doc_hash = hashlib.md5(f"{file.filename}_{len(content)}".encode() + content).hexdigest()
        
        for c in chunks:
            c.metadata["document_id"] = doc_hash
            
        logger.info("Checking for already processed chunks in Qdrant...")
        existing_ids = await asyncio.to_thread(
            qdrant_manager.get_existing_chunk_ids, collection_name, doc_hash
        )
        
        remaining_chunks = [c for c in chunks if c.chunk_id not in existing_ids]
        
        if existing_ids:
            logger.info(
                f"Resuming upload: Found {len(existing_ids)} already processed chunks. "
                f"Processing {len(remaining_chunks)} remaining chunks."
            )
            
        if not remaining_chunks:
            logger.info("All chunks already exist in Qdrant. Upload complete.")
            processing_time = time.time() - start_time
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return UploadResponse(
                success=True,
                chunks_created=len(chunks),
                processing_time=processing_time,
                message=f"Document '{file.filename}' already completely processed. Skipped {len(existing_ids)} existing chunks."
            )

        BATCH_SIZE = 20
        total_batches = (len(remaining_chunks) + BATCH_SIZE - 1) // BATCH_SIZE
        
        logger.info(f"Processing {len(remaining_chunks)} remaining chunks in {total_batches} batches...")
        
        for batch_idx in range(total_batches):
            batch_start = batch_idx * BATCH_SIZE
            batch_end = min(batch_start + BATCH_SIZE, len(remaining_chunks))
            batch_chunks = remaining_chunks[batch_start:batch_end]
            batch_texts = [c.text for c in batch_chunks]
            
            logger.info(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_chunks)} chunks)...")
            
            try:
                # Generate embeddings for batch
                embeddings = await asyncio.to_thread(embedding_manager.generate_all_embeddings, batch_texts)
                
                # Store points in Qdrant
                await asyncio.to_thread(qdrant_manager.store_points, collection_name, batch_chunks, embeddings)
                
            except ConnectionError as e:
                logger.error(f"Database connection failed during storage: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=503,
                    detail=f"Connection failed during batch {batch_idx + 1}. You can retry uploading to resume where it left off."
                )
            except Exception as e:
                logger.error(f"Failed processing batch {batch_idx + 1}: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed during batch {batch_idx + 1}. You can retry uploading to resume. Error: {str(e)}"
                )
        
        logger.info(f"Successfully processed and stored all {len(remaining_chunks)} remaining chunks")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Step 7: Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"Cleaned up temporary file: {temp_file_path}")
        
        # Return success response
        logger.info(
            f"Upload complete - File: {file.filename}, "
            f"Total Chunks: {len(chunks)}, Processed Now: {len(remaining_chunks)}, Time: {processing_time:.2f}s"
        )
        
        return UploadResponse(
            success=True,
            chunks_created=len(chunks),
            processing_time=processing_time,
            message=f"Successfully uploaded '{file.filename}'. Processed {len(remaining_chunks)} chunks in {processing_time:.2f}s. (Skipped {len(existing_ids)} already processed)"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except ValueError as e:
        logger.error(f"Validation error during upload: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during upload: {str(e)}"
        )
        
    finally:
        # Ensure temporary file is cleaned up even if an error occurs
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temporary file in finally block: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {str(e)}")


# Query Endpoint

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Execute multi-stage retrieval and generate answer.

    Flow:
    1. Validate query and collection
    2. Generate query embeddings using EmbeddingModelManager
    3. Execute retrieval pipeline using MultiEmbeddingRetrievalPipeline.retrieve
    4. Generate answer using LLMClient.generate_answer
    5. Return QueryResponse with answer, sources, and timing metrics

    Args:
        request: Contains query text and collection_name

    Returns:
        QueryResponse with answer and sources

    Raises:
        HTTPException(400): If query or collection invalid
        HTTPException(404): If no relevant documents found
        HTTPException(503): If database or LLM connection fails
        HTTPException(504): If operation times out
        HTTPException(500): If retrieval or LLM fails
    """
    retrieval_start_time = time.time()
    generation_start_time = None
    
    try:
        logger.info(
            f"Starting query - Query: '{request.query[:100]}...', "
            f"Collection: {request.collection_name}"
        )
        
        # Step 1: Validate query text and collection_name
        query_text = request.query.strip()
        collection_name = request.collection_name.strip()
        
        if not query_text:
            logger.warning("Empty query text provided")
            raise HTTPException(
                status_code=400,
                detail="Query text cannot be empty. Please provide a question or search query."
            )
        
        if not collection_name:
            logger.warning("Empty collection name provided")
            raise HTTPException(
                status_code=400,
                detail="Collection name cannot be empty. Please select a collection."
            )
        
        # Validate collection exists with timeout
        logger.info(f"Validating collection: {collection_name}")
        try:
            existing_collections = await asyncio.wait_for(
                asyncio.to_thread(qdrant_manager.list_collections),
                timeout=DATABASE_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error("Database search timeout")
            raise HTTPException(
                status_code=504,
                detail="Database search operation timed out (timeout). Please try again."
            )
        except ConnectionError as e:
            logger.error(f"Database connection failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to database: {str(e)}. Please ensure Qdrant is running."
            )
        
        if collection_name not in existing_collections:
            logger.warning(f"Collection not found: {collection_name}")
            raise HTTPException(
                status_code=400,
                detail=f"Collection '{collection_name}' does not exist. Available collections: {', '.join(existing_collections) if existing_collections else 'none'}"
            )
        
        # Step 2-3: Execute retrieval pipeline with timeout
        logger.info("Executing retrieval pipeline...")
        try:
            retrieval_results = await asyncio.wait_for(
                asyncio.to_thread(
                    retrieval_pipeline.retrieve,
                    query=query_text,
                    collection_name=collection_name,
                    use_cross_encoder=True
                ),
                timeout=NETWORK_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Document retrieval timed out (timeout) after {NETWORK_TIMEOUT}s")
            raise HTTPException(
                status_code=504,
                detail=f"Document retrieval timed out (timeout) after {NETWORK_TIMEOUT}s. The collection may be very large."
            )
        except ValueError as e:
            logger.error(f"Validation error during retrieval: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Validation error: {str(e)}"
            )
        except ConnectionError as e:
            logger.error(f"Database connection failed during retrieval: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail=f"Database connection error during retrieval: {str(e)}"
            )
        except RuntimeError as e:
            logger.error(f"Retrieval pipeline failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Retrieval failed: {str(e)}. This may be due to embedding model issues."
            )
        except Exception as e:
            logger.error(f"Unexpected error during retrieval: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error during retrieval: {str(e)}"
            )
        
        retrieval_time = time.time() - retrieval_start_time
        logger.info(f"Retrieval complete: {len(retrieval_results)} results in {retrieval_time:.3f}s")
        
        # Step 4: Handle no results case
        if not retrieval_results:
            logger.info("No relevant documents found for query")
            raise HTTPException(
                status_code=404,
                detail="No relevant documents found for your query. Try rephrasing your question or uploading more documents to the collection."
            )
        
        # Step 5: Generate answer using LLM with timeout
        logger.info(f"Generating answer with LLM using {len(retrieval_results)} context chunks...")
        generation_start_time = time.time()
        
        try:
            # Extract context chunks from retrieval results
            context_chunks = [result.text for result in retrieval_results]
            
            # Generate answer with timeout
            answer = await asyncio.wait_for(
                asyncio.to_thread(
                    llm_client.generate_answer,
                    query=query_text,
                    context_chunks=context_chunks
                ),
                timeout=LLM_TIMEOUT
            )
            
            generation_time = time.time() - generation_start_time
            logger.info(f"Answer generated in {generation_time:.3f}s")
            
        except asyncio.TimeoutError:
            generation_time = time.time() - generation_start_time if generation_start_time else 0.0
            logger.error(f"LLM generation timed out (timeout) after {LLM_TIMEOUT}s")
            raise HTTPException(
                status_code=504,
                detail=f"Answer generation timed out (timeout) after {LLM_TIMEOUT}s. The LLM server may be overloaded or the context is too large."
            )
        except ConnectionError as e:
            generation_time = time.time() - generation_start_time if generation_start_time else 0.0
            logger.error(f"LLM connection failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to LLM server: {str(e)}. Please ensure Ollama is running and accessible."
            )
        except Exception as e:
            generation_time = time.time() - generation_start_time if generation_start_time else 0.0
            logger.error(f"LLM generation failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Answer generation failed: {str(e)}. This may be due to LLM server issues or invalid context."
            )
        
        # Step 6: Return QueryResponse with answer, sources, and timing metrics
        total_time = time.time() - retrieval_start_time
        logger.info(
            f"Query complete - Sources: {len(retrieval_results)}, "
            f"Total time: {total_time:.3f}s (retrieval: {retrieval_time:.3f}s, generation: {generation_time:.3f}s)"
        )
        
        return QueryResponse(
            answer=answer,
            sources=retrieval_results,
            retrieval_time=retrieval_time,
            generation_time=generation_time
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error during query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during query processing: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 80)
    logger.info(f"Starting Uvicorn server on {BACKEND_HOST}:{BACKEND_PORT}")
    logger.info("=" * 80)
    
    uvicorn.run(
        app,
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        log_level="info"
    )

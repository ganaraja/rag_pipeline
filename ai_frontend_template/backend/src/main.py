"""
FastAPI application template for AI applications.

This template provides the reusable structure for:
- FastAPI setup with CORS
- Qdrant integration
- Error handling and logging
- Request middleware
- Health check endpoint
- Collection management endpoints

Customize by adding your AI-specific endpoints below.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import logging
import time
import os
import asyncio
from datetime import datetime, timezone

from models import (
    CreateCollectionRequest,
    CreateCollectionResponse,
    DeleteCollectionResponse,
)
from qdrant_manager import QdrantManager

# Environment variable configuration
QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant_db")
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Startup logging
logger.info("=" * 80)
logger.info("AI Application - Backend Server Starting")
logger.info("=" * 80)
logger.info(f"Qdrant Path: {QDRANT_PATH}")
logger.info(f"Backend Host: {BACKEND_HOST}")
logger.info(f"Backend Port: {BACKEND_PORT}")
logger.info("=" * 80)

# Timeout configurations (in seconds)
DATABASE_TIMEOUT = 10.0

# Initialize FastAPI app
app = FastAPI(
    title="AI Application API",
    description="REST API for AI-powered application",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Qdrant manager
logger.info("Initializing Qdrant manager...")
qdrant_manager = QdrantManager(path=QDRANT_PATH)
logger.info("✓ Qdrant manager initialized")

logger.info("=" * 80)
logger.info("All components initialized successfully!")
logger.info("=" * 80)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing information."""
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
    logger.error(f"Validation error at {error_context['path']}: {str(exc)}")
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
    """Handle timeout errors."""
    error_context = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "method": request.method,
        "error_type": "TimeoutError"
    }
    logger.error(f"Timeout error at {error_context['path']}")
    return JSONResponse(
        status_code=504,
        content={
            "detail": "The operation took too long to complete.",
            "error_type": "timeout_error",
            "timestamp": error_context["timestamp"]
        }
    )


@app.exception_handler(ConnectionError)
async def connection_error_handler(request: Request, exc: ConnectionError):
    """Handle connection errors."""
    error_context = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "method": request.method,
        "error_type": "ConnectionError"
    }
    logger.error(f"Connection error at {error_context['path']}: {str(exc)}")
    
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Failed to connect to required services.",
            "error_type": "connection_error",
            "timestamp": error_context["timestamp"]
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    error_context = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "method": request.method,
        "error_type": type(exc).__name__
    }
    logger.error(
        f"Unexpected error at {error_context['path']}: {str(exc)}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "error_type": "internal_server_error",
            "timestamp": error_context["timestamp"]
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# Collection Management Endpoints (Reusable)

@app.get("/api/collections", response_model=List[str])
async def list_collections():
    """List all collections in Qdrant."""
    try:
        logger.info("Fetching collections from Qdrant")
        
        collections = await asyncio.wait_for(
            asyncio.to_thread(qdrant_manager.list_collections),
            timeout=DATABASE_TIMEOUT
        )
        
        logger.info(f"Successfully listed {len(collections)} collections")
        return collections
        
    except asyncio.TimeoutError:
        logger.error("Database operation timed out")
        raise HTTPException(status_code=504, detail="Operation timed out")
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/collections", response_model=CreateCollectionResponse)
async def create_collection(request: CreateCollectionRequest):
    """Create a new collection."""
    try:
        collection_name = request.collection_name.strip()
        if not collection_name:
            raise HTTPException(status_code=400, detail="Collection name cannot be empty")
        
        logger.info(f"Creating collection: {collection_name}")
        
        # Check if exists
        existing = await asyncio.wait_for(
            asyncio.to_thread(qdrant_manager.list_collections),
            timeout=DATABASE_TIMEOUT
        )
        
        if collection_name in existing:
            raise HTTPException(status_code=409, detail=f"Collection '{collection_name}' already exists")
        
        # Create collection
        await asyncio.wait_for(
            asyncio.to_thread(qdrant_manager.create_collection, collection_name),
            timeout=DATABASE_TIMEOUT
        )
        
        logger.info(f"Successfully created collection: {collection_name}")
        
        return CreateCollectionResponse(
            success=True,
            collection_name=collection_name,
            message=f"Collection '{collection_name}' created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/collections/{name}", response_model=DeleteCollectionResponse)
async def delete_collection(name: str):
    """Delete a collection."""
    try:
        collection_name = name.strip()
        logger.info(f"Deleting collection: {collection_name}")
        
        # Check if exists
        existing = await asyncio.wait_for(
            asyncio.to_thread(qdrant_manager.list_collections),
            timeout=DATABASE_TIMEOUT
        )
        
        if collection_name not in existing:
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
        
        # Delete collection
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
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# TODO: Add your custom API endpoints here
# Example:
# @app.post("/api/your-endpoint")
# async def your_endpoint(request: YourRequestModel):
#     """Your custom endpoint logic."""
#     try:
#         # Your implementation here
#         result = process_your_data(request)
#         return {"success": True, "data": result}
#     except Exception as e:
#         logger.error(f"Error in your_endpoint: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)

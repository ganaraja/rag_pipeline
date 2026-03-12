"""
FastAPI application for RAG Full-Stack Application.

This module provides the REST API endpoints for collection management,
document upload, and query operations.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import logging
import time
from datetime import datetime, timezone

from models import (
    CreateCollectionRequest,
    CreateCollectionResponse,
    DeleteCollectionResponse,
)
from qdrant_manager import QdrantManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Initialize Qdrant manager
qdrant_manager = QdrantManager()


# Request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests with timing information."""
    start_time = time.time()
    
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - Time: {process_time:.3f}s")
    
    return response


# Global exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions with 400 Bad Request."""
    logger.error(f"ValueError: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions with 500 Internal Server Error."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"}
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
        HTTPException(500): If Qdrant connection fails
    """
    try:
        collections = qdrant_manager.list_collections()
        logger.info(f"Listed {len(collections)} collections")
        return collections
    except Exception as e:
        logger.error(f"Failed to list collections: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list collections: {str(e)}"
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
        HTTPException(500): If creation fails
    """
    try:
        # Validate collection name
        collection_name = request.collection_name.strip()
        if not collection_name:
            raise HTTPException(
                status_code=400,
                detail="Collection name cannot be empty"
            )
        
        # Check if collection already exists
        existing_collections = qdrant_manager.list_collections()
        if collection_name in existing_collections:
            raise HTTPException(
                status_code=409,
                detail=f"Collection '{collection_name}' already exists"
            )
        
        # Create collection
        qdrant_manager.create_collection(collection_name)
        logger.info(f"Created collection: {collection_name}")
        
        return CreateCollectionResponse(
            success=True,
            collection_name=collection_name,
            message=f"Collection '{collection_name}' created successfully"
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error creating collection: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create collection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create collection: {str(e)}"
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
        HTTPException(404): If collection doesn't exist
        HTTPException(500): If deletion fails
    """
    try:
        # Check if collection exists
        existing_collections = qdrant_manager.list_collections()
        if name not in existing_collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{name}' does not exist"
            )
        
        # Delete collection
        qdrant_manager.delete_collection(name)
        logger.info(f"Deleted collection: {name}")
        
        return DeleteCollectionResponse(
            success=True,
            message=f"Collection '{name}' deleted successfully"
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error deleting collection: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete collection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete collection: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

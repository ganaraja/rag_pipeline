"""
Generic FastAPI application for AI applications with Qdrant.

This is a template that can be extended for specific AI applications.
"""

import os
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from TEMPLATE_MODELS import (
    CreateCollectionRequest,
    CreateCollectionResponse,
    DeleteCollectionResponse,
    ListCollectionsResponse,
    CollectionInfoResponse,
    StorePointsRequest,
    StorePointsResponse,
    SearchRequest,
    SearchResponse,
    HealthCheckResponse,
    ErrorResponse,
    DocumentChunk
)
from TEMPLATE_QDRANT_MANAGER import QdrantManager

# Initialize FastAPI app
app = FastAPI(
    title="AI Application API",
    description="Generic API for AI applications with Qdrant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Qdrant Manager
qdrant_manager = QdrantManager(
    mode=os.getenv("QDRANT_MODE", "embedded"),
    path=os.getenv("QDRANT_PATH", "./qdrant_db"),
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=os.getenv("QDRANT_PORT", "6333"),
    api_key=os.getenv("QDRANT_API_KEY")
)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check if the API and Qdrant are accessible."""
    qdrant_accessible = qdrant_manager.health_check()
    
    if qdrant_accessible:
        return HealthCheckResponse(
            status="healthy",
            qdrant_accessible=True,
            message="API and Qdrant are accessible"
        )
    else:
        return HealthCheckResponse(
            status="unhealthy",
            qdrant_accessible=False,
            message="Qdrant is not accessible"
        )


@app.get("/api/collections", response_model=ListCollectionsResponse)
async def list_collections():
    """List all collections in Qdrant."""
    try:
        collections = qdrant_manager.list_collections()
        return ListCollectionsResponse(
            collections=collections,
            count=len(collections)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list collections: {str(e)}"
        )


@app.post("/api/collections", response_model=CreateCollectionResponse)
async def create_collection(request: CreateCollectionRequest):
    """Create a new collection in Qdrant."""
    try:
        qdrant_manager.create_collection(
            collection_name=request.collection_name,
            vector_size=request.vector_size,
            distance=request.distance
        )
        
        return CreateCollectionResponse(
            success=True,
            collection_name=request.collection_name,
            message=f"Collection '{request.collection_name}' created successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create collection: {str(e)}"
        )


@app.delete("/api/collections/{collection_name}", response_model=DeleteCollectionResponse)
async def delete_collection(collection_name: str):
    """Delete a collection from Qdrant."""
    try:
        qdrant_manager.delete_collection(collection_name)
        
        return DeleteCollectionResponse(
            success=True,
            message=f"Collection '{collection_name}' deleted successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete collection: {str(e)}"
        )


@app.get("/api/collections/{collection_name}/info", response_model=CollectionInfoResponse)
async def get_collection_info(collection_name: str):
    """Get information about a collection."""
    try:
        info = qdrant_manager.get_collection_info(collection_name)
        return CollectionInfoResponse(**info)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collection info: {str(e)}"
        )


@app.post("/api/store", response_model=StorePointsResponse)
async def store_points(request: StorePointsRequest):
    """Store document chunks with embeddings in Qdrant."""
    try:
        # Convert chunks to dict format for Qdrant manager
        chunks_dict = [
            {
                "id": chunk.id,
                "text": chunk.text,
                "meta": chunk.meta
            }
            for chunk in request.chunks
        ]
        
        qdrant_manager.store_points(
            collection_name=request.collection_name,
            embeddings=request.embeddings,
            chunks=chunks_dict
        )
        
        return StorePointsResponse(
            success=True,
            points_stored=len(request.chunks),
            message=f"Stored {len(request.chunks)} points in collection '{request.collection_name}'"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store points: {str(e)}"
        )


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search for similar vectors in a collection."""
    try:
        results = qdrant_manager.search(
            collection_name=request.collection_name,
            query_vector=request.query_vector,
            limit=request.limit
        )
        
        return SearchResponse(
            results=results,
            count=len(results),
            collection_name=request.collection_name
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search: {str(e)}"
        )


# Example endpoint for file upload (customize for your needs)
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    collection_name: str = Form(...)
):
    """
    Example endpoint for file upload.
    
    Note: This is a template. You need to implement:
    1. File parsing/extraction
    2. Chunking strategy
    3. Embedding generation
    4. Then call store_points()
    """
    try:
        # Read file content
        content = await file.read()
        
        # TODO: Implement file parsing, chunking, and embedding generation
        # For now, return a placeholder response
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"File '{file.filename}' uploaded to collection '{collection_name}'",
                "filename": file.filename,
                "collection_name": collection_name,
                "note": "Implement file processing, chunking, and embedding generation"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            status_code=exc.status_code
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000"))
    )
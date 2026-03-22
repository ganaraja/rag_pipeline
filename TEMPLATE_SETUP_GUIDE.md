# AI Frontend Template - Setup Guide

## Overview

This template provides a generic foundation for building AI applications with:
- **Qdrant vector database** (embedded and server modes)
- **FastAPI backend** with RESTful API
- **Generic models** for collection management and search
- **Production-ready configuration** with environment variables

## Files to Copy

Copy these files to your template repository:

### Backend Files
```
~/repos/ai_frontend_template/backend/src/
├── qdrant_manager.py    # Copy from: rag_pipeline/TEMPLATE_QDRANT_MANAGER.py
├── models.py            # Copy from: rag_pipeline/TEMPLATE_MODELS.py
└── main.py              # Copy from: rag_pipeline/TEMPLATE_MAIN.py (rename as needed)
```

### Configuration Files
```
~/repos/ai_frontend_template/
├── .env.template        # Copy from: rag_pipeline/.env.template
└── pyproject.toml       # Update with dependencies (see below)
```

## Dependencies

Add these to your `pyproject.toml`:

```toml
[project]
name = "ai-frontend-template"
version = "1.0.0"
description = "Template for AI applications with Qdrant"
requires-python = ">=3.10"

dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "qdrant-client>=1.7.0",
    "python-multipart>=0.0.6",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
]
```

## Quick Start

### 1. Copy Files
```bash
# Copy backend files
cp rag_pipeline/TEMPLATE_QDRANT_MANAGER.py ~/repos/ai_frontend_template/backend/src/qdrant_manager.py
cp rag_pipeline/TEMPLATE_MODELS.py ~/repos/ai_frontend_template/backend/src/models.py
cp rag_pipeline/TEMPLATE_MAIN.py ~/repos/ai_frontend_template/backend/src/main.py

# Copy configuration
cp rag_pipeline/.env.template ~/repos/ai_frontend_template/.env.template
```

### 2. Configure Environment
```bash
cd ~/repos/ai_frontend_template
cp .env.template .env
# Edit .env as needed
```

### 3. Install Dependencies
```bash
cd ~/repos/ai_frontend_template/backend
uv sync
```

### 4. Start the Application
```bash
# Start backend
cd ~/repos/ai_frontend_template/backend
uv run python -m src.main

# Or with environment variables
QDRANT_MODE=embedded API_PORT=8000 uv run python -m src.main
```

### 5. Test the API
```bash
# Health check
curl http://localhost:8000/health

# List collections
curl http://localhost:8000/api/collections

# Create a collection
curl -X POST http://localhost:8000/api/collections \
  -H "Content-Type: application/json" \
  -d '{"collection_name": "test-collection", "vector_size": 768}'
```

## API Endpoints

### Collection Management
- `GET /health` - Health check
- `GET /api/collections` - List all collections
- `POST /api/collections` - Create a new collection
- `DELETE /api/collections/{name}` - Delete a collection
- `GET /api/collections/{name}/info` - Get collection info

### Data Operations
- `POST /api/store` - Store document chunks with embeddings
- `POST /api/search` - Search for similar vectors
- `POST /api/upload` - Example file upload endpoint

## Configuration

### Qdrant Modes

#### Embedded Mode (Development)
```bash
QDRANT_MODE=embedded
QDRANT_PATH=./qdrant_db
```

#### Server Mode (Production)
```bash
QDRANT_MODE=server
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=  # For Qdrant Cloud
```

### API Configuration
```bash
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Extending the Template

### 1. Add Custom Models
Edit `models.py` to add your application-specific models:

```python
# Add to models.py
class YourCustomRequest(BaseModel):
    query: str
    parameters: Dict[str, Any]

class YourCustomResponse(BaseModel):
    results: List[Dict[str, Any]]
    processing_time: float
```

### 2. Add Custom Endpoints
Edit `main.py` to add your application endpoints:

```python
# Add to main.py
@app.post("/api/custom-endpoint")
async def custom_endpoint(request: YourCustomRequest):
    # Your implementation here
    pass
```

### 3. Extend Qdrant Manager
Override methods in `qdrant_manager.py` for custom behavior:

```python
# Create a custom manager
class CustomQdrantManager(QdrantManager):
    def create_collection(self, collection_name: str, custom_config: Dict):
        # Custom collection creation
        pass
    
    def custom_search(self, collection_name: str, query: str, filters: Dict):
        # Custom search with filters
        pass
```

### 4. Add File Processing
Implement file parsing, chunking, and embedding generation:

```python
# Example in main.py
@app.post("/api/process-document")
async def process_document(file: UploadFile, collection_name: str):
    # 1. Parse document
    text = parse_document(await file.read())
    
    # 2. Chunk text
    chunks = chunk_text(text)
    
    # 3. Generate embeddings
    embeddings = generate_embeddings([chunk.text for chunk in chunks])
    
    # 4. Store in Qdrant
    await store_points(StorePointsRequest(
        collection_name=collection_name,
        embeddings=embeddings,
        chunks=chunks
    ))
```

## Testing

### Run Tests
```bash
cd ~/repos/ai_frontend_template/backend
uv run pytest tests/ -v
```

### Example Test
```python
# tests/test_qdrant_manager.py
import pytest
from src.qdrant_manager import QdrantManager

def test_create_collection():
    manager = QdrantManager(mode="embedded", path="./test_qdrant_db")
    manager.create_collection("test-collection")
    collections = manager.list_collections()
    assert "test-collection" in collections
```

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
RUN pip install uv && uv sync

COPY backend/src/ ./src/

CMD ["uv", "run", "python", "-m", "src.main"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - QDRANT_MODE=server
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    depends_on:
      - qdrant

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
```

## Best Practices

### 1. Environment Variables
- Use `.env` for local development
- Use environment variables in production
- Never commit `.env` to version control

### 2. Error Handling
- Use proper HTTP status codes
- Return descriptive error messages
- Log errors for debugging

### 3. Security
- Validate all inputs
- Use CORS appropriately
- Consider authentication for production

### 4. Performance
- Use batching for embeddings
- Implement pagination for large results
- Cache frequently accessed data

## Troubleshooting

### Qdrant Connection Issues
```bash
# Check if Qdrant is running
curl http://localhost:6333/collections

# Check logs
docker logs qdrant_container_name
```

### API Issues
```bash
# Check if API is running
curl http://localhost:8000/health

# Check logs
uv run python -m src.main
```

### Dependency Issues
```bash
# Reinstall dependencies
uv sync --clean

# Check Python version
python --version
```

## Next Steps

1. **Add Frontend** - Create React/Vue frontend
2. **Add Authentication** - Implement user authentication
3. **Add Monitoring** - Add logging and metrics
4. **Add CI/CD** - Set up automated testing and deployment
5. **Add Documentation** - Create API documentation

## Support

For issues:
1. Check the logs
2. Verify environment variables
3. Test Qdrant connection
4. Review API documentation at `http://localhost:8000/docs`

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
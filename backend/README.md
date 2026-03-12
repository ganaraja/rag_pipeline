# RAG Backend API

FastAPI backend for the RAG Full-Stack Application.

## Running the Server

### Development Mode

```bash
cd backend
PYTHONPATH=src uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or use the Python module directly:

```bash
cd backend
PYTHONPATH=src python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
cd backend
PYTHONPATH=src python src/main.py
```

The server will start on `http://localhost:8000`

## API Endpoints

### Health Check

- `GET /health` - Health check endpoint

### Collection Management

- `GET /api/collections` - List all collections
- `POST /api/collections` - Create a new collection
  - Body: `{"collection_name": "my_collection"}`
- `DELETE /api/collections/{name}` - Delete a collection

## Running Tests

```bash
cd backend
PYTHONPATH=src pytest tests/ -v
```

Run specific test file:

```bash
cd backend
PYTHONPATH=src pytest tests/test_api_collections.py -v
```

## API Documentation

Once the server is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

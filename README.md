# RAG Full-Stack Application

A full-stack Retrieval-Augmented Generation (RAG) system with sophisticated multi-embedding retrieval pipelines. This application enables document ingestion, intelligent semantic search, and AI-powered question-answering using multiple embedding strategies.

## Features

- **Multi-Embedding Retrieval**: Combines Matryoshka (64D/768D), ColBERT, and SPLADE embeddings for optimal search accuracy
- **Document Processing**: Sophisticated chunking pipeline using Docling and Chonkie for semantic coherence
- **Admin Interface**: React-based UI for collection and document management
- **Chat Interface**: Interactive Q&A interface for querying documents
- **Vector Database**: Qdrant for efficient multi-vector storage and retrieval
- **LLM Integration**: Ollama for natural language answer generation

## Architecture

```
┌─────────────────┐
│  React Frontend │
│  (Admin + Chat) │
└────────┬────────┘
         │ HTTP/REST
┌────────▼────────┐
│  FastAPI Backend│
│  - Chunking     │
│  - Embeddings   │
│  - Retrieval    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────┐
│Qdrant│  │Ollama │
│Vector│  │  LLM  │
│  DB  │  │Server │
└──────┘  └───────┘
```

## Prerequisites

Before setting up the application, ensure you have the following installed:

- **Python** >= 3.10
- **Node.js** >= 18
- **UV** (Python package manager)
- **Ollama** (LLM inference server)

## Setup Instructions

### 1. Install UV (Python Package Manager)

UV is a fast Python package manager that replaces pip. Install it using:

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify installation:
```bash
uv --version
```

### 2. Install Ollama (LLM Server)

Ollama provides local LLM inference. Install it from [ollama.ai](https://ollama.ai):

```bash
# On macOS
brew install ollama

# On Linux
curl -fsSL https://ollama.ai/install.sh | sh

# On Windows
# Download installer from https://ollama.ai/download
```

Start Ollama and pull a model:
```bash
# Start Ollama server (runs in background)
ollama serve

# In a new terminal, pull a model
ollama pull llama3.2
# Or use a larger model like:
# ollama pull mistral
```

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

### 3. Backend Setup

#### Install Python Dependencies

From the project root directory:

```bash
# Using UV (recommended - fast and reliable)
uv sync

# Or using pip (alternative)
pip install -e ".[dev]"
```

This installs all required packages including:
- FastAPI, Uvicorn (web framework)
- Qdrant client (vector database)
- Sentence-transformers (embedding models)
- Docling, Chonkie (document processing)
- OpenAI client (Ollama-compatible)
- Pytest (testing)

#### Configure Backend Environment

Create a `.env` file in the project root directory:

```bash
# Copy the template
cp .env.template .env
```

The `.env.template` file contains all available configuration options with detailed comments. Key settings to review:

```bash
# Qdrant Configuration
QDRANT_MODE=embedded              # Use "server" for production
QDRANT_PATH=./qdrant_db          # For embedded mode
QDRANT_HOST=localhost             # For server mode
QDRANT_PORT=6333                  # For server mode
QDRANT_API_KEY=                   # For Qdrant Cloud

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
LLM_TIMEOUT=60

# Embedding Models
MATRYOSHKA_MODEL=jinaai/jina-embeddings-v3
COLBERT_MODEL=colbert-ir/colbertv2.0
SPLADE_MODEL=naver/splade-v3
DEVICE=cpu                        # Use "cuda" for GPU, "mps" for Apple Silicon

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

See `.env.template` for complete documentation of all configuration options.

#### Qdrant Setup

Qdrant is the vector database used for storing and retrieving document embeddings. This application supports two modes:

##### Embedded Mode (Development - Default)

Qdrant runs **in-process** with your application - no separate installation needed!

- Data is stored locally in the `./qdrant_db` directory
- Automatically created when you start the backend
- Perfect for development and testing
- No additional setup required

**Configuration** (in `.env`):
```bash
QDRANT_MODE=embedded
QDRANT_PATH=./qdrant_db
```

##### Server Mode (Production - Recommended)

Qdrant runs as a separate service, providing better performance and scalability.

**Option 1: Docker (Recommended)**

```bash
# Run Qdrant in Docker
docker run -d \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  --name qdrant \
  qdrant/qdrant

# Verify it's running
curl http://localhost:6333/collections
```

**Option 2: Qdrant Cloud**

1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create a cluster
3. Get your API key and cluster URL

**Configuration** (in `.env`):
```bash
# For local Docker
QDRANT_MODE=server
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=  # Leave empty for local Docker

# For Qdrant Cloud
QDRANT_MODE=server
QDRANT_HOST=your-cluster.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your-api-key-here
```

**When to use each mode:**
- **Embedded**: Development, testing, single-user applications
- **Server**: Production, multi-user applications, better performance

### 4. Frontend Setup

#### Install Node.js Dependencies

```bash
cd frontend
npm install
```

This installs:
- React, React-DOM (UI framework)
- TypeScript (type safety)
- Vite (build tool)
- Axios (HTTP client)
- Jest, React Testing Library (testing)

#### Configure Frontend Environment

Create a `.env` file in the `frontend/` directory:

```bash
cp .env.example .env
```

Edit `.env` if needed:
```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```

## Running the Application

### Quick Start (Using Convenience Scripts)

We provide startup scripts for easy launching:

```bash
# Start backend (checks Ollama and dependencies first)
./start_backend.sh

# In a new terminal, start frontend
./start_frontend.sh
```

### Manual Start

#### Start Backend Server

From the project root:

```bash
# Make sure Ollama is running first!
# ollama serve

# Start backend with environment variables loaded
cd backend
python -m src.main

# Or with custom settings
OLLAMA_MODEL=mistral EMBEDDING_DEVICE=cuda python -m src.main
```

The backend will start on `http://localhost:8000`. You should see:
```
RAG Full-Stack Application - Backend Server Starting
Qdrant Path: ./qdrant_db
Ollama Base URL: http://localhost:11434/v1
...
All components initialized successfully!
```

### Start Frontend Development Server

In a new terminal:

```bash
cd frontend
npm run dev
```

The frontend will start on `http://localhost:3000` with hot-reload enabled.

### Access the Application

1. **Admin Interface**: `http://localhost:3000` - Create collections and upload documents
2. **Chat Interface**: `http://localhost:3000` - Ask questions about your documents
3. **API Docs**: `http://localhost:8000/docs` - Interactive API documentation

## Running Tests

### Backend Tests

Run all backend tests with pytest:

```bash
# From project root
PYTHONPATH=backend/src pytest backend/tests/

# With coverage report
PYTHONPATH=backend/src pytest backend/tests/ --cov=backend/src --cov-report=html

# Run specific test file
PYTHONPATH=backend/src pytest backend/tests/test_api_query.py

# Run with verbose output
PYTHONPATH=backend/src pytest backend/tests/ -v
```

### Frontend Tests

Run frontend tests with Jest:

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode (for development)
npm run test:watch

# Run with coverage
npm run test:coverage
```

### Integration Tests

Run end-to-end integration tests:

```bash
# Make sure both backend and frontend are running
PYTHONPATH=backend/src pytest tests/
```

## Usage Guide

### 1. Create a Collection

1. Open the admin interface at `http://localhost:3000`
2. Click "Create Collection"
3. Enter a collection name (e.g., "my-documents")
4. Click "Create"

### 2. Upload Documents

1. Select your collection from the dropdown
2. Click "Choose File" and select a document (PDF, Word, Markdown, or TXT)
3. Click "Upload"
4. Wait for processing to complete (chunking + embedding generation)

### 3. Ask Questions

1. Navigate to the chat interface
2. Select your collection
3. Type a question in the input field
4. Press Enter or click "Send"
5. View the AI-generated answer with source references

## Project Structure

```
rag_pipeline/
├── backend/                    # FastAPI backend
│   ├── src/
│   │   ├── main.py            # API endpoints & startup
│   │   ├── models.py          # Pydantic data models
│   │   ├── qdrant_manager.py  # Vector database operations
│   │   ├── chunking_strategy.py # Document processing
│   │   ├── embedding_manager.py # Multi-embedding generation
│   │   ├── retrieval_pipeline.py # Multi-stage search
│   │   └── llm_client.py      # Ollama integration
│   ├── tests/                 # Backend tests
│   ├── .env.example           # Environment variables template
│   └── pytest.ini             # Pytest configuration
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API client
│   │   └── App.tsx            # Main application
│   ├── tests/                 # Frontend tests
│   ├── .env.example           # Environment variables template
│   ├── vite.config.ts         # Vite build configuration
│   └── package.json           # Node.js dependencies
├── tests/                      # Integration tests
├── qdrant_db/                  # Qdrant local database (auto-created)
├── start_backend.sh            # Backend startup script
├── start_frontend.sh           # Frontend startup script
├── pyproject.toml              # Python dependencies (UV)
├── README.md                   # This file
└── .gitignore                  # Git ignore rules
```

## API Endpoints

### Collection Management

- `GET /api/collections` - List all collections
- `POST /api/collections` - Create a new collection
- `DELETE /api/collections/{name}` - Delete a collection

### Document Operations

- `POST /api/upload` - Upload and process a document
  - Form data: `file` (document), `collection_name` (string)

### Query Operations

- `POST /api/query` - Query documents and get AI answer
  - JSON body: `{"query": "...", "collection_name": "..."}`

### Health Check

- `GET /health` - Server health status

## Configuration Reference

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_MODE` | `embedded` | Qdrant mode: "embedded" or "server" |
| `QDRANT_PATH` | `./qdrant_db` | Path for embedded Qdrant database |
| `QDRANT_HOST` | `localhost` | Qdrant server host (server mode) |
| `QDRANT_PORT` | `6333` | Qdrant server port (server mode) |
| `QDRANT_API_KEY` | `` | Qdrant API key (optional) |
| `QDRANT_COLLECTION` | `documents` | Default collection name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.2` | LLM model name |
| `LLM_TIMEOUT` | `60` | LLM request timeout (seconds) |
| `LLM_MAX_RETRIES` | `3` | Max retries for LLM requests |
| `MATRYOSHKA_MODEL` | `jinaai/jina-embeddings-v3` | Matryoshka embedding model |
| `COLBERT_MODEL` | `colbert-ir/colbertv2.0` | ColBERT model |
| `SPLADE_MODEL` | `naver/splade-v3` | SPLADE model |
| `CROSS_ENCODER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Reranking model |
| `DEVICE` | `cpu` | Device for embeddings (cpu/cuda/mps/auto) |
| `API_HOST` | `0.0.0.0` | Server bind address |
| `API_PORT` | `8000` | Server port |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Allowed CORS origins |
| `USE_PREFETCH` | `true` | Enable multi-stage retrieval |
| `ENABLE_CROSS_ENCODER` | `true` | Enable reranking |
| `ENABLE_CONTEXTUAL_CHUNKING` | `true` | Add context to chunks |
| `ENABLE_LATE_CHUNKING` | `true` | Use late chunking strategy |

See `.env.template` for complete documentation.

### Frontend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |

## Troubleshooting

### Backend Issues

**Problem**: `Connection refused` to Ollama
- **Solution**: Ensure Ollama is running: `ollama serve`

**Problem**: `CUDA out of memory` error
- **Solution**: Set `EMBEDDING_DEVICE=cpu` in backend/.env

**Problem**: Slow embedding generation
- **Solution**: Use GPU if available: `EMBEDDING_DEVICE=cuda` (NVIDIA) or `EMBEDDING_DEVICE=mps` (Apple Silicon)

**Problem**: Qdrant database errors
- **Solution (Embedded mode)**: Delete `./qdrant_db` directory and restart backend to recreate
- **Solution (Server mode)**: Verify Qdrant server is running: `curl http://localhost:6333/collections`
- **Solution (Server mode)**: Check Docker container: `docker ps | grep qdrant`

**Problem**: `Storage folder is already accessed by another instance`
- **Solution**: Only one process can access embedded Qdrant at a time. Stop other instances or use server mode for concurrent access

**Problem**: Qdrant connection refused (server mode)
- **Solution**: Ensure Qdrant server is running: `docker start qdrant` or start Docker container
- **Solution**: Check QDRANT_HOST and QDRANT_PORT in .env match your Qdrant server

### Frontend Issues

**Problem**: `Cannot connect to backend`
- **Solution**: Ensure backend is running on port 8000

**Problem**: CORS errors
- **Solution**: Check that frontend is running on port 3000 (configured in backend CORS)

### General Issues

**Problem**: Tests failing
- **Solution**: Ensure `PYTHONPATH=backend/src` is set when running backend tests

**Problem**: Import errors
- **Solution**: Reinstall dependencies: `uv sync` (backend) or `npm install` (frontend)

## Development

### Building for Production

#### Backend
```bash
# Backend runs directly with Python
python -m src.main
```

#### Frontend
```bash
cd frontend
npm run build
# Output in frontend/dist/

# Preview production build
npm run preview
```

### Code Quality

```bash
# Backend linting (if configured)
cd backend
pylint src/

# Frontend linting
cd frontend
npm run lint  # (if configured)
```

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Qdrant**: Vector database for embeddings
- **Sentence-Transformers**: Embedding model library
- **Docling**: Document parsing
- **Chonkie**: Semantic chunking
- **Ollama**: Local LLM inference

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool
- **Axios**: HTTP client
- **Jest**: Testing framework

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions:
- Check the troubleshooting section above
- Review API documentation at `http://localhost:8000/docs`
- Check Ollama status: `ollama list`
- Verify Qdrant database: `ls -la qdrant_db/`

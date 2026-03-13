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

Create a `.env` file in the `backend/` directory:

```bash
cd backend
cp .env.example .env
```

Edit `.env` to customize settings (optional):
```bash
# backend/.env
QDRANT_PATH=./qdrant_db
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
EMBEDDING_DEVICE=cpu  # Use 'cuda' for GPU, 'mps' for Apple Silicon
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

#### Qdrant Setup (Local Mode)

Qdrant runs in **local mode** by default - no separate installation needed! The vector database is stored in the `./qdrant_db` directory and is automatically created when you start the backend.

**Note**: For production deployments, you can use Qdrant Cloud or a self-hosted Qdrant server. Update `QDRANT_PATH` to a Qdrant URL if using a remote instance.

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
| `QDRANT_PATH` | `./qdrant_db` | Path to Qdrant database directory |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama API endpoint |
| `OLLAMA_MODEL` | `gpt-oss:20b` | LLM model name |
| `EMBEDDING_DEVICE` | `cpu` | Device for embeddings (cpu/cuda/mps) |
| `BACKEND_HOST` | `0.0.0.0` | Server bind address |
| `BACKEND_PORT` | `8000` | Server port |

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
- **Solution**: Delete `./qdrant_db` directory and restart backend to recreate

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

# RAG Full-Stack Application

A full-stack Retrieval-Augmented Generation (RAG) system with multi-embedding retrieval pipelines.

## Project Structure

```
rag_pipeline/
├── frontend/           # React + TypeScript frontend
│   ├── src/           # Source code
│   ├── tests/         # Jest tests
│   ├── package.json   # Frontend dependencies
│   ├── tsconfig.json  # TypeScript configuration
│   ├── jest.config.ts # Jest configuration
│   └── vite.config.ts # Vite configuration
├── backend/           # FastAPI backend
│   ├── src/          # Source code
│   ├── tests/        # Pytest tests
│   └── pytest.ini    # Pytest configuration
├── tests/            # Integration tests
├── pyproject.toml    # Python dependencies (UV)
└── README.md         # This file
```

## Setup Instructions

### Backend Setup (Python with UV)

1. Install UV (if not already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install dependencies:

```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -e ".[dev]"
```

3. Run backend tests:

```bash
PYTHONPATH=backend/src pytest backend/tests/
```

### Frontend Setup (Node.js)

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Run frontend tests:

```bash
npm test
```

3. Run development server:

```bash
npm run dev
```

## Dependencies

### Backend Dependencies

- FastAPI: Web framework
- Uvicorn: ASGI server
- Qdrant: Vector database client
- Sentence-transformers: Embedding models
- Docling: Document parsing
- Chonkie: Semantic chunking
- OpenAI: LLM client (Ollama compatible)
- Pytest: Testing framework

### Frontend Dependencies

- React: UI framework
- TypeScript: Type safety
- Vite: Build tool
- Jest: Test runner
- React Testing Library: Component testing

## Requirements

- Python >= 3.10
- Node.js >= 18
- UV (for Python dependency management)

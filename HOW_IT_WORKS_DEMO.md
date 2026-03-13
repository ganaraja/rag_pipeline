# RAG Full-Stack Application - How It Works Demo

## Overview

This document demonstrates the complete workflow of the RAG (Retrieval-Augmented Generation) application, from setup to querying documents.

## Architecture Flow

```
User → Frontend (React) → Backend API (FastAPI) → Qdrant (Vector DB) + Ollama (LLM)
```

## Step-by-Step Demonstration

### 1. Prerequisites Setup

#### Install UV (Python Package Manager)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
uv --version
```

#### Install Ollama (LLM Server)
```bash
# macOS
brew install ollama

# Start Ollama
ollama serve

# Pull a model (in another terminal)
ollama pull llama3.2
```

### 2. Backend Setup

```bash
# Install dependencies
uv sync

# Create environment file
cp backend/.env.example backend/.env

# Edit backend/.env if needed (defaults work for local setup)
```

**Backend Configuration** (`backend/.env`):
```env
QDRANT_PATH=./qdrant_db
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
EMBEDDING_DEVICE=cpu
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit frontend/.env if needed
```

**Frontend Configuration** (`frontend/.env`):
```env
VITE_API_URL=http://localhost:8000
```

### 4. Start the Application

#### Terminal 1: Start Backend
```bash
# From project root
uv run uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000

# Or use convenience script
./start_backend.sh
```

**Expected Output**:
```
================================================================================
RAG Full-Stack Application - Backend Server Starting
================================================================================
Qdrant Path: ./qdrant_db
Ollama Base URL: http://localhost:11434/v1
Ollama Model: llama3.2
Embedding Device: cpu
Backend Host: 0.0.0.0
Backend Port: 8000
================================================================================
INFO:     Initializing Qdrant Manager...
INFO:     Initializing Chunking Strategy...
INFO:     Initializing Embedding Manager...
INFO:     Initializing Retrieval Pipeline...
INFO:     Initializing LLM Client...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Terminal 2: Start Frontend
```bash
cd frontend
npm run dev

# Or use convenience script
./start_frontend.sh
```

**Expected Output**:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### 5. Using the Application

#### Access the Application
Open your browser to: **http://localhost:3000**

---

## Workflow Demonstration

### Phase 1: Collection Management (Admin Interface)

#### Step 1: Create a Collection
1. Navigate to the **Admin** tab
2. Click **"Create Collection"** button
3. Enter collection name: `my-documents`
4. Click **"Submit"**

**What Happens Behind the Scenes**:
```
Frontend → POST /api/collections
         → Backend validates name (alphanumeric, hyphens, underscores)
         → Qdrant creates collection with multi-vector configuration:
            - matryoshka_64 (64D dense vectors)
            - matryoshka_768 (768D dense vectors)
            - colbert (128D multi-vectors)
            - splade (sparse vectors)
         → Returns success
```

**API Request**:
```json
POST /api/collections
{
  "collection_name": "my-documents"
}
```

**API Response**:
```json
{
  "success": true,
  "collection_name": "my-documents",
  "message": "Collection 'my-documents' created successfully with multi-vector configuration"
}
```

#### Step 2: View Collections
The dropdown automatically refreshes and shows `my-documents`

**API Call**:
```
GET /api/collections
→ Returns: ["my-documents"]
```

---

### Phase 2: Document Upload

#### Step 1: Select Collection
Choose `my-documents` from the dropdown

#### Step 2: Upload a Document
1. Click **"Choose File"**
2. Select a document (PDF, Word, Markdown, or TXT)
3. Click **"Upload"**

**Example Document** (`sample.txt`):
```
Python Programming Language

Python is a high-level, interpreted programming language known for its 
simplicity and readability. Created by Guido van Rossum and first released 
in 1991, Python emphasizes code readability with its notable use of 
significant indentation.

Python supports multiple programming paradigms, including procedural, 
object-oriented, and functional programming. It has a comprehensive 
standard library and a large ecosystem of third-party packages.

Key Features:
- Easy to learn and use
- Extensive standard library
- Cross-platform compatibility
- Large community support
- Versatile for web development, data science, AI, and more
```

**What Happens Behind the Scenes**:

1. **File Upload**:
```
Frontend → POST /api/upload (multipart/form-data)
         → Backend receives file and collection_name
```

2. **Document Parsing** (Docling):
```
Backend → Docling parses document structure
        → Extracts parent chunks (sections, paragraphs)
        → Preserves document hierarchy
```

3. **Semantic Chunking** (Chonkie):
```
Backend → Chonkie splits text into semantic chunks
        → Maintains coherent meaning boundaries
        → Creates ~3-5 chunks from sample document
```

4. **Embedding Generation**:
```
Backend → EmbeddingModelManager generates 4 types of embeddings:
        
        For each chunk:
        ├─ Matryoshka 64D: [0.123, -0.456, ..., 0.789] (64 dimensions)
        ├─ Matryoshka 768D: [0.123, -0.456, ..., 0.321] (768 dimensions)
        ├─ ColBERT: [[0.1, ...], [0.2, ...], ...] (multi-vector, 128D each)
        └─ SPLADE: {indices: [1, 5, 23, ...], values: [0.8, 0.6, 0.4, ...]}
```

5. **Vector Storage** (Qdrant):
```
Backend → QdrantManager stores points in Qdrant:
        
        Point {
          id: 1,
          vector: {
            "matryoshka_64": [64D vector],
            "matryoshka_768": [768D vector],
            "colbert": [multi-vectors],
            "splade": {sparse vector}
          },
          payload: {
            text: "Python is a high-level...",
            chunk_id: 1,
            parent_id: 0,
            metadata: {...}
          }
        }
```

**API Response**:
```json
{
  "success": true,
  "chunks_created": 5,
  "processing_time": 2.34,
  "message": "Successfully uploaded and processed 'sample.txt'. Created 5 chunks in 2.34s."
}
```

**Processing Timeline**:
```
0.0s  → File received
0.1s  → Docling parsing complete
0.5s  → Semantic chunking complete
1.8s  → Embedding generation complete (all 4 types)
2.3s  → Qdrant storage complete
2.34s → Response sent
```

---

### Phase 3: Querying Documents (Chat Interface)

#### Step 1: Switch to Chat Tab
Click the **"Chat"** tab

#### Step 2: Select Collection
Ensure `my-documents` is selected

#### Step 3: Ask a Question
Type: **"What is Python and what are its key features?"**

**What Happens Behind the Scenes**:

1. **Query Embedding Generation**:
```
Frontend → POST /api/query
Backend → EmbeddingModelManager generates query embeddings:
        ├─ Matryoshka 64D
        ├─ Matryoshka 768D
        ├─ ColBERT
        └─ SPLADE
```

2. **Multi-Stage Retrieval**:

**Stage 1: Dense Retrieval (Matryoshka 64D)**
```
Backend → Qdrant searches using 64D vectors
        → Fast initial retrieval
        → Returns top 100 candidates
        → Scores: [0.95, 0.88, 0.82, ...]
```

**Stage 2: Prefetch Refinement (Matryoshka 768D)**
```
Backend → Qdrant refines with 768D vectors
        → More precise similarity
        → Filters to top 50 candidates
        → Scores: [0.96, 0.91, 0.85, ...]
```

**Stage 3: ColBERT Multi-Vector Matching**
```
Backend → Qdrant uses ColBERT multi-vectors
        → Token-level matching
        → Filters to top 20 candidates
        → Scores: [0.97, 0.93, 0.87, ...]
```

**Stage 4: SPLADE Sparse Matching**
```
Backend → Qdrant applies SPLADE sparse vectors
        → Keyword-based refinement
        → Filters to top 10 candidates
        → Scores: [0.98, 0.94, 0.89, ...]
```

**Stage 5: Cross-Encoder Reranking**
```
Backend → Cross-encoder reranks final candidates
        → Deep semantic understanding
        → Returns top 5 results
        → Final scores: [0.99, 0.95, 0.91, 0.88, 0.85]
```

3. **Context Construction**:
```
Backend → Extracts text from top 5 chunks:
        
        Context = [
          "Python is a high-level, interpreted programming language...",
          "Python supports multiple programming paradigms...",
          "Key Features: Easy to learn and use...",
          "Created by Guido van Rossum in 1991...",
          "Extensive standard library and ecosystem..."
        ]
```

4. **LLM Answer Generation** (Ollama):
```
Backend → LLMClient constructs prompt:
        
        System: You are a helpful assistant...
        
        Context:
        [1] Python is a high-level, interpreted programming language...
        [2] Python supports multiple programming paradigms...
        [3] Key Features: Easy to learn and use...
        [4] Created by Guido van Rossum in 1991...
        [5] Extensive standard library and ecosystem...
        
        Question: What is Python and what are its key features?
        
        Answer:

Backend → Ollama (llama3.2) generates answer
        → Streams response token by token
        → Returns complete answer
```

**API Response**:
```json
{
  "answer": "Python is a high-level, interpreted programming language created by Guido van Rossum in 1991. It is known for its simplicity, readability, and use of significant indentation. Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.\n\nKey features of Python include:\n- Easy to learn and use\n- Extensive standard library\n- Cross-platform compatibility\n- Large community support\n- Versatile for web development, data science, AI, and more",
  "sources": [
    {
      "id": 1,
      "text": "Python is a high-level, interpreted programming language...",
      "score": 0.99,
      "distance": 0.01,
      "metadata": {"chunk_id": 1, "parent_id": 0}
    },
    {
      "id": 3,
      "text": "Python supports multiple programming paradigms...",
      "score": 0.95,
      "distance": 0.05,
      "metadata": {"chunk_id": 3, "parent_id": 0}
    },
    ...
  ],
  "retrieval_time": 0.234,
  "generation_time": 1.567
}
```

**Query Timeline**:
```
0.0s   → Query received
0.05s  → Query embeddings generated
0.23s  → Multi-stage retrieval complete (5 stages)
1.80s  → LLM answer generation complete
1.80s  → Response sent
```

#### Step 4: View Results
The chat interface displays:
- **Answer**: Generated by LLM based on retrieved context
- **Sources**: Expandable cards showing the 5 source chunks used
- **Timing**: Retrieval time (0.23s) and Generation time (1.57s)

---

## Advanced Features

### 1. Multiple Collections
```bash
# Create different collections for different document types
- technical-docs
- user-manuals
- research-papers
```

### 2. Batch Document Upload
Upload multiple documents to the same collection sequentially

### 3. Collection Deletion
Delete collections when no longer needed (with confirmation)

### 4. Error Handling
The application handles:
- Invalid file formats
- Missing collections
- Empty queries
- Connection failures
- Timeout errors

---

## Performance Characteristics

### Document Processing
- **Small documents** (< 1 page): ~1-2 seconds
- **Medium documents** (5-10 pages): ~5-10 seconds
- **Large documents** (50+ pages): ~30-60 seconds

### Query Response Time
- **Retrieval**: 0.1-0.5 seconds (depends on collection size)
- **LLM Generation**: 1-3 seconds (depends on answer length)
- **Total**: 1.5-3.5 seconds typical

### Scalability
- **Collections**: Unlimited
- **Documents per collection**: Thousands
- **Chunks per document**: Hundreds
- **Concurrent queries**: Multiple (async handling)

---

## API Endpoints Summary

### Collection Management
- `GET /api/collections` - List all collections
- `POST /api/collections` - Create new collection
- `DELETE /api/collections/{name}` - Delete collection

### Document Operations
- `POST /api/upload` - Upload and process document

### Query Operations
- `POST /api/query` - Query documents and generate answer

### Health Check
- `GET /health` - Check API health

---

## Technology Stack

### Backend
- **FastAPI**: REST API framework
- **Qdrant**: Vector database (local mode)
- **Ollama**: LLM inference (llama3.2)
- **Docling**: Document parsing
- **Chonkie**: Semantic chunking
- **sentence-transformers**: Embedding models
- **UV**: Python package manager

### Frontend
- **React**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Axios**: HTTP client
- **Jest**: Testing framework

### Embedding Models
- **Matryoshka**: Dense embeddings (64D, 768D)
- **ColBERT**: Multi-vector embeddings (128D per token)
- **SPLADE**: Sparse embeddings (keyword-based)
- **Cross-encoder**: Reranking model

---

## Conclusion

The RAG Full-Stack Application provides a complete, production-ready solution for:
- Document ingestion and processing
- Sophisticated multi-embedding retrieval
- LLM-powered question answering
- User-friendly web interface

All components work together seamlessly to deliver accurate, context-aware answers to user queries based on uploaded documents.

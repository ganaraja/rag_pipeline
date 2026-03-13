# AI Frontend Template

A standalone, reusable template for building AI-powered full-stack applications with React + TypeScript frontend and FastAPI + Qdrant backend.

## ✨ Key Features

- **100% Independent**: No dependencies on parent projects
- **Production-Ready**: Complete error handling, logging, and validation
- **Fully Tested**: Test suites for both frontend and backend
- **Well-Documented**: Comprehensive guides and examples
- **Quick Start**: Startup scripts included

## 📦 What's Included

### Frontend (React + TypeScript)
- Complete Vite + TypeScript setup
- Collection management components (create, list, delete)
- File uploader component
- Chat interface component
- API service layer with error handling
- TypeScript type definitions
- Test suite with Jest and React Testing Library

### Backend (Python + FastAPI)
- FastAPI application with CORS
- Generic Qdrant integration (easily extensible)
- Request logging middleware
- Comprehensive error handling
- Health check endpoint
- Collection management endpoints
- Test suite with pytest

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- UV (Python package manager)

### Setup

1. **Backend**:
```bash
cd backend
uv sync
cp .env.example .env
```

2. **Frontend**:
```bash
cd frontend
npm install
cp .env.example .env
```

### Run

```bash
# Terminal 1 - Backend
./start_backend.sh

# Terminal 2 - Frontend
./start_frontend.sh
```

### Verify
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs
- Health: http://localhost:8000/health

## 📁 Project Structure

```
ai_frontend_template/
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI app (add your endpoints)
│   │   ├── models.py            # Pydantic models (add your models)
│   │   ├── qdrant_manager.py    # Qdrant integration (extend as needed)
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_api_collections.py
│   │   └── __init__.py
│   ├── pyproject.toml
│   ├── pytest.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── services/            # API service layer
│   │   ├── types/               # TypeScript types
│   │   ├── config/              # Configuration
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── .env.example
├── start_backend.sh
├── start_frontend.sh
├── .gitignore
└── README.md (this file)
```

## 🔧 Customization

### Add Custom API Endpoint

Edit `backend/src/main.py`:

```python
@app.post("/api/your-endpoint")
async def your_endpoint(request: YourRequestModel):
    try:
        # Your logic here
        result = process_data(request)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Add Custom Model

Edit `backend/src/models.py`:

```python
class YourRequestModel(BaseModel):
    field1: str
    field2: int
```

### Add Custom Frontend Component

Create `frontend/src/components/YourComponent.tsx`:

```typescript
export const YourComponent = () => {
  return <div>Your UI</div>;
};
```

### Extend Qdrant Manager

Edit `backend/src/qdrant_manager.py` to override methods for custom vector configurations.

## 🧪 Testing

```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests
cd frontend
npm test
```

## 📚 Documentation

- **README.md** (this file) - Quick start and overview
- **TEMPLATE_GUIDE.md** - Detailed usage guide
- **QUICK_REFERENCE.md** - Command reference
- **INSTALLATION.md** - Setup instructions

## ⚡ Time Savings

This template saves approximately **7-11 days** of development time by providing:
- Frontend setup and components: 2-3 days
- Backend API structure: 2-3 days
- Qdrant integration: 1-2 days
- Testing setup: 1-2 days
- Documentation: 1 day

## 🎯 Use Cases

Perfect for:
- RAG applications
- Semantic search engines
- AI chatbots
- Document analysis tools
- Image/audio similarity search
- Any AI app with vector database

## 📝 License

MIT - Free to use for any project

## 🆘 Support

Check the documentation files for detailed guidance:
- Setup issues → INSTALLATION.md
- Customization → TEMPLATE_GUIDE.md
- Commands → QUICK_REFERENCE.md

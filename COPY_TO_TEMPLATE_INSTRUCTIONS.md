# Instructions for Copying to Template Repository

## Files to Copy to `~/repos/ai_frontend_template/`

### 1. Backend Source Files
Copy these to `~/repos/ai_frontend_template/backend/src/`:

1. **Qdrant Manager** (Generic Version)
   ```bash
   cp rag_pipeline/TEMPLATE_QDRANT_MANAGER.py ~/repos/ai_frontend_template/backend/src/qdrant_manager.py
   ```

2. **Pydantic Models** (Generic Models)
   ```bash
   cp rag_pipeline/TEMPLATE_MODELS.py ~/repos/ai_frontend_template/backend/src/models.py
   ```

3. **Main Application** (FastAPI App)
   ```bash
   cp rag_pipeline/TEMPLATE_MAIN.py ~/repos/ai_frontend_template/backend/src/main.py
   ```

### 2. Configuration Files
Copy to template root:
```bash
# Environment template
cp rag_pipeline/.env.template ~/repos/ai_frontend_template/.env.template

# Setup guide
cp rag_pipeline/TEMPLATE_SETUP_GUIDE.md ~/repos/ai_frontend_template/SETUP_GUIDE.md
```

### 3. Dependencies
Add to `pyproject.toml` in template:
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
    "python-dotenv>=1.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0"
]
```

### 4. Quick Start Commands
```bash
# 1. Copy files to template
cp rag_pipeline/TEMPLATE_QDRANT_MANAGER.py ~/repos/ai_frontend_template/backend/src/qdrant_manager.py
cp rag_pipeline/TEMPLATE_MODELS.py ~/repos/ai_frontend_template/backend/src/models.py
cp rag_pipeline/TEMPLATE_MAIN.py ~/repos/ai_frontend_template/backend/src/main.py
cp rag_pipeline/.env.template ~/repos/ai_frontend_template/.env.template
cp rag_pipeline/TEMPLATE_SETUP_GUIDE.md ~/repos/ai_frontend_template/SETUP_GUIDE.md

# 2. Update pyproject.toml with dependencies
# 3. Copy setup guide to template
```

### 5. Template Structure After Copying
```
~/repos/ai_frontend_template/
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI application
│   │   ├── qdrant_manager.py    # Generic Qdrant manager
│   │   └── models.py            # Pydantic models
│   ├── tests/
│   └── pyproject.toml
├── .env.template
├── SETUP_GUIDE.md
└── README.md
```

### 6. Key Features in Template

**Generic Qdrant Manager Features:**
- ✅ Embedded & server mode support
- ✅ Collection management
- ✅ Point storage with batching
- ✅ Vector search
- ✅ Health checks
- ✅ Error handling

**API Endpoints:**
- `GET /health` - Health check
- `GET /api/collections` - List collections
- `POST /api/collections` - Create collection
- `DELETE /api/collections/{name}` - Delete collection
- `POST /api/store` - Store embeddings
- `POST /api/search` - Search vectors
- `POST /api/upload` - File upload endpoint

### 7. Quick Test
After copying files:
```bash
# Navigate to template
cd ~/repos/ai_frontend_template/backend

# Install dependencies
uv sync

# Run the application
uv run python -m src.main
```

### 8. Verification
Test the API:
```bash
# Health check
curl http://localhost:8000/health

# List collections (should be empty initially)
curl http://localhost:8000/api/collections
```

### 9. Customization Points
1. **Extend models.py** - Add your data models
2. **Extend main.py** - Add custom endpoints
3. **Extend qdrant_manager.py** - Add custom methods
4. **Update .env.template** - Add your environment variables

### 10. Production Notes
- Set `QDRANT_MODE=server` for production
- Use environment variables for secrets
- Add authentication middleware
- Add request logging
- Add monitoring (Prometheus, Grafana)
- Add rate limiting
- Add request validation
- Add comprehensive error handling

### 11. Next Steps After Copying
1. Update README.md with template-specific instructions
2. Add example usage and code samples
3. Add tests for the template
4. Create example projects
5. Add deployment scripts
6. Add CI/CD configuration

### 12. Verification Checklist
- [ ] All files copied to template
- [ ] Dependencies updated in pyproject.toml
- [ ] Environment variables documented
- [ ] API endpoints documented
- [ ] Example usage provided
- [ ] Tests pass
- [ ] README updated with setup instructions

This template provides a production-ready foundation for AI applications with Qdrant vector database support.
#!/bin/bash
# Startup script for RAG Backend Server

echo "=========================================="
echo "RAG Backend Server - Startup Script"
echo "=========================================="

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✓ Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠ No .env file found, using defaults"
    echo "  (Copy .env.template to .env to customize)"
fi

# Check if Ollama is running (warn but don't exit - backend can start without it)
echo ""
echo "Checking Ollama server..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running"
else
    echo "⚠ Ollama is not running - LLM queries will fail"
    echo "  Start Ollama with: ollama serve"
fi

# Check if dependencies are installed
echo ""
echo "Checking Python dependencies..."
if uv run python -c "import fastapi" 2>/dev/null; then
    echo "✓ Dependencies installed"
else
    echo "✗ Dependencies not installed!"
    echo "  Please run: uv sync"
    exit 1
fi

# Start the backend server
echo ""
echo "Starting backend server..."
echo "  API:  http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo "=========================================="
cd backend && PYTHONPATH=src uv run python src/main.py

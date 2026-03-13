#!/bin/bash
# Startup script for RAG Backend Server

echo "=========================================="
echo "RAG Backend Server - Startup Script"
echo "=========================================="

# Check if .env file exists
if [ -f "backend/.env" ]; then
    echo "✓ Loading environment variables from backend/.env"
    export $(cat backend/.env | grep -v '^#' | xargs)
else
    echo "⚠ No backend/.env file found, using defaults"
    echo "  (Copy backend/.env.example to backend/.env to customize)"
fi

# Check if Ollama is running
echo ""
echo "Checking Ollama server..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running"
else
    echo "✗ Ollama is not running!"
    echo "  Please start Ollama first: ollama serve"
    exit 1
fi

# Check if dependencies are installed
echo ""
echo "Checking Python dependencies..."
if python3 -c "import fastapi" 2>/dev/null; then
    echo "✓ Dependencies installed"
else
    echo "✗ Dependencies not installed!"
    echo "  Please run: uv sync"
    exit 1
fi

# Start the backend server
echo ""
echo "Starting backend server..."
echo "=========================================="
cd backend && python3 -m src.main

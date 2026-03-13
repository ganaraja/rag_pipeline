#!/bin/bash
# Startup script for RAG Frontend

echo "=========================================="
echo "RAG Frontend - Startup Script"
echo "=========================================="

# Check if .env file exists
if [ -f "frontend/.env" ]; then
    echo "✓ Loading environment variables from frontend/.env"
else
    echo "⚠ No frontend/.env file found, using defaults"
    echo "  (Copy frontend/.env.example to frontend/.env to customize)"
fi

# Check if node_modules exists
if [ -d "frontend/node_modules" ]; then
    echo "✓ Dependencies installed"
else
    echo "✗ Dependencies not installed!"
    echo "  Please run: cd frontend && npm install"
    exit 1
fi

# Check if backend is running
echo ""
echo "Checking backend server..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is running"
else
    echo "⚠ Backend is not running!"
    echo "  The frontend will work but API calls will fail"
    echo "  Start backend first: ./start_backend.sh"
fi

# Start the frontend development server
echo ""
echo "Starting frontend development server..."
echo "=========================================="
cd frontend && npm run dev

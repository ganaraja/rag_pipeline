#!/bin/bash

# Start the backend server

echo "Starting AI Backend Server..."
echo "=============================="

cd backend

# Check if .env exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Start the server
echo "Starting FastAPI server..."
uv run python src/main.py

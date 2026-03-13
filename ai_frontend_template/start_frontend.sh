#!/bin/bash

# Start the frontend development server

echo "Starting AI Frontend Server..."
echo "==============================="

cd frontend

# Check if .env exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the development server
echo "Starting Vite development server..."
npm run dev

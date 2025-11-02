#!/bin/bash

# Binance Live Quant Analytics - Quick Start Script

echo "🚀 Starting Binance Live Quant Analytics..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."
pip show fastapi > /dev/null || (echo "Installing dependencies..." && pip install -r requirements.txt)

# Create data directory
mkdir -p data

# Start backend in background
echo "🔧 Starting backend (port 8000)..."
python backend/main.py &
BACKEND_PID=$!

sleep 3

# Start frontend
echo "🎨 Starting frontend (port 8501)..."
streamlit run frontend/app.py

# Cleanup
kill $BACKEND_PID 2>/dev/null

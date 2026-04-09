#!/bin/bash
# Run Heritage Lens Streamlit UI via Docker

set -e

echo "🏛️  Heritage Lens Streamlit Launcher"
echo "===================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and run
echo "📦 Building Streamlit container..."
docker-compose build streamlit

echo ""
echo "🚀 Starting Streamlit UI..."
docker-compose up -d streamlit

echo ""
echo "⏳ Waiting for Streamlit to be ready..."
sleep 5

# Check if running
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo ""
    echo "✅ Streamlit is running!"
    echo ""
    echo "🌐 Access the UI at: http://localhost:8501"
    echo ""
    echo "📊 View logs: docker-compose logs -f streamlit"
    echo "🛑 Stop: docker-compose stop streamlit"
else
    echo ""
    echo "⚠️  Streamlit may still be starting..."
    echo "🌐 Try accessing: http://localhost:8501 in a few seconds"
    echo ""
    echo "📊 View logs: docker-compose logs -f streamlit"
fi

#!/bin/bash
# Start Cloudflare Tunnel for Heritage Lens
# Usage: ./start-cloudflare-tunnel.sh

echo "=========================================="
echo "Starting Cloudflare Tunnel"
echo "=========================================="
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared not found. Run setup-cloudflare-tunnel.sh first"
    exit 1
fi

# Check if Streamlit is running
if ! curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "⚠️  Streamlit is not running on port 8501"
    echo "   Start it first: docker-compose up -d streamlit"
    exit 1
fi

echo "🚀 Starting Cloudflare Tunnel..."
echo "   Local: http://localhost:8501"
echo ""
echo "⏳ Your HTTPS URL will appear below (look for 'Your quick Tunnel'):"
echo "=========================================="
echo ""

# Run the tunnel with a trycloudflare.com temporary URL
# This is free and doesn't require a Cloudflare account or domain
cloudflared tunnel --url http://localhost:8501

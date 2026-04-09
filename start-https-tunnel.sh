#!/bin/bash
# Start HTTPS tunnel for Heritage Lens Streamlit dashboard
# Usage: ./start-https-tunnel.sh [subdomain]

SUBDOMAIN=${1:-heritage-ar26}

echo "🚀 Starting HTTPS tunnel for Streamlit..."
echo "   Local: http://localhost:8501"
echo "   Public: https://$SUBDOMAIN.loca.lt"
echo ""
echo "⚠️  IMPORTANT:"
echo "   1. This script will display your public HTTPS URL"
echo "   2. Share that URL with your hackathon judges"
echo "   3. Press Ctrl+C to stop the tunnel"
echo ""
echo "=========================================="

lt --port 8501 --subdomain "$SUBDOMAIN"

#!/bin/bash
# Setup Cloudflare Tunnel for Heritage Lens HTTPS access
# Cloudflare Tunnel provides free, secure HTTPS without connection limits

set -e

echo "=========================================="
echo "Cloudflare Tunnel Setup for Heritage Lens"
echo "=========================================="
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing cloudflared..."

    # Detect architecture
    ARCH=$(uname -m)
    if [[ "$ARCH" == "x86_64" ]]; then
        CF_ARCH="amd64"
    elif [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
        CF_ARCH="arm64"
    else
        CF_ARCH="amd64"
    fi

    # Download and install cloudflared
    LATEST_VERSION=$(curl -s https://api.github.com/repos/cloudflare/cloudflared/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    DOWNLOAD_URL="https://github.com/cloudflare/cloudflared/releases/download/${LATEST_VERSION}/cloudflared-linux-${CF_ARCH}"

    echo "   Downloading cloudflared ${LATEST_VERSION} for ${CF_ARCH}..."
    curl -sL "$DOWNLOAD_URL" -o /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/
    sudo chmod +x /usr/local/bin/cloudflared

    echo "✅ cloudflared installed: $(cloudflared version | head -1)"
else
    echo "✅ cloudflared found: $(cloudflared version | head -1)"
fi

echo ""

# Check if Streamlit is running
echo "🔍 Checking if Streamlit is running..."
if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "✅ Streamlit is running on port 8501"
else
    echo "⚠️  Streamlit not detected on port 8501"
    echo "   Please start Streamlit first:"
    echo "   cd ~/heritage-lens-multimodal && docker-compose up -d streamlit"
    echo ""
fi

# Create the tunnel startup script
cat > ~/start-cloudflare-tunnel.sh << 'INNEREOF'
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
INNEREOF

chmod +x ~/start-cloudflare-tunnel.sh

echo ""
echo "=========================================="
echo "✅ Cloudflare Tunnel Setup Complete!"
echo "=========================================="
echo ""
echo "🚀 Quick Start (Temporary URL - No account needed):"
echo "   ./start-cloudflare-tunnel.sh"
echo ""
echo "   This gives you a free temporary HTTPS URL like:"
echo "   https://random-words.trycloudflare.com"
echo ""
echo "🌐 Permanent URL (Requires Cloudflare account + domain):"
echo "   If you have a Cloudflare account and domain, run:"
echo "   cloudflared tunnel login"
echo "   cloudflared tunnel create heritage-lens"
echo "   cloudflared tunnel route dns heritage-lens heritage.yourdomain.com"
echo "   cloudflared tunnel run heritage-lens"
echo ""
echo "💡 Comparison:"
echo "   ┌──────────────┬──────────────┬─────────────────┐"
echo "   │ Feature      │ ngrok Free   │ Cloudflare      │"
echo "   ├──────────────┼──────────────┼─────────────────┤"
echo "   │ Connection   │ 1 hour max   │ Unlimited       │"
echo "   │ limit        │              │                 │"
echo "   │ Rate limits  │ 40/min       │ None            │"
echo "   │ Custom domain│ \$8/month    │ Free            │"
echo "   │ Account req. │ Optional     │ Only for custom │"
echo "   └──────────────┴──────────────┴─────────────────┘"
echo ""
echo "🎯 For the hackathon demo, run:"
echo "   ./start-cloudflare-tunnel.sh"
echo ""

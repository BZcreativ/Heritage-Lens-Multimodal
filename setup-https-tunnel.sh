#!/bin/bash
# Setup HTTPS tunnel for Heritage Lens Streamlit dashboard
# Uses LocalTunnel for quick, secure public access

set -e

echo "=========================================="
echo "Heritage Lens HTTPS Tunnel Setup"
echo "=========================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Installing..."

    # Install Node.js (using NodeSource for latest LTS)
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs

    echo "✅ Node.js installed: $(node --version)"
else
    echo "✅ Node.js found: $(node --version)"
fi

# Install LocalTunnel globally
echo ""
echo "📦 Installing LocalTunnel..."
sudo npm install -g localtunnel

# Check if Streamlit is running
echo ""
echo "🔍 Checking if Streamlit is running..."
if curl -s http://localhost:8501/_stcore/health > /dev/null; then
    echo "✅ Streamlit is running on port 8501"
else
    echo "⚠️  Streamlit not detected on port 8501"
    echo "   Please start Streamlit first:"
    echo "   cd ~/heritage-lens-multimodal && docker-compose up streamlit"
    echo ""
    read -p "Press Enter when Streamlit is running..."
fi

# Create tunnel startup script
cat > ~/start-https-tunnel.sh << 'EOF'
#!/bin/bash
# Start HTTPS tunnel for Heritage Lens
# Usage: ./start-https-tunnel.sh [subdomain]

SUBDOMAIN=${1:-heritage-lens}

echo "🚀 Starting HTTPS tunnel for Streamlit..."
echo "   Local: http://localhost:8501"
echo "   Subdomain: $SUBDOMAIN"
echo ""
echo "⚠️  IMPORTANT: On first connection, you'll see:"
echo "   'your url is: https://heritage-lens.loca.lt'"
echo ""
echo "   Click the link and complete the tunnel authentication."
echo "   Then share the HTTPS URL with your team."
echo ""
echo "   Press Ctrl+C to stop the tunnel"
echo "=========================================="

lt --port 8501 --subdomain "$SUBDOMAIN"
EOF

chmod +x ~/start-https-tunnel.sh

# Create ngrok alternative script too (as backup)
cat > ~/start-ngrok-tunnel.sh << 'EOF'
#!/bin/bash
# Alternative: Start HTTPS tunnel using ngrok
# Usage: ./start-ngrok-tunnel.sh

echo "🚀 Starting ngrok HTTPS tunnel for Streamlit..."
echo "   Local: http://localhost:8501"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found. Installing..."

    # Download ngrok
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
        sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
        sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update
    sudo apt install ngrok

    echo ""
    echo "⚠️  ngrok requires authtoken setup:"
    echo "   1. Sign up at https://dashboard.ngrok.com/signup"
    echo "   2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "   3. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    exit 1
fi

echo "✅ ngrok found"
echo "   Starting tunnel to port 8501..."
echo "   Your HTTPS URL will appear below:"
echo "=========================================="

ngrok http 8501
EOF

chmod +x ~/start-ngrok-tunnel.sh

# Create systemd service for persistent tunnel (optional)
cat > ~/setup-tunnel-service.sh << 'EOF'
#!/bin/bash
# Setup systemd service for persistent HTTPS tunnel
# Note: Requires authentication on first run

SERVICE_NAME="heritage-tunnel"
SUBDOMAIN=${1:-heritage-lens}

cat > /tmp/$SERVICE_NAME.service << EOF
[Unit]
Description=Heritage Lens HTTPS Tunnel
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/bin/lt --port 8501 --subdomain $SUBDOMAIN
Restart=always
RestartSec=10
Environment="NODE_ENV=production"

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/$SERVICE_NAME.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "✅ Systemd service created: $SERVICE_NAME"
echo ""
echo "Commands:"
echo "  sudo systemctl start $SERVICE_NAME   # Start tunnel"
echo "  sudo systemctl stop $SERVICE_NAME    # Stop tunnel"
echo "  sudo systemctl enable $SERVICE_NAME  # Auto-start on boot"
echo "  sudo systemctl status $SERVICE_NAME  # Check status"
EOF

chmod +x ~/setup-tunnel-service.sh

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "🚀 Quick Start:"
echo "   ./start-https-tunnel.sh              # Start with random URL"
echo "   ./start-https-tunnel.sh my-demo      # Start with custom subdomain"
echo ""
echo "🔗 Alternative (ngrok):"
echo "   ./start-ngrok-tunnel.sh              # Requires ngrok account"
echo ""
echo "⚙️  Persistent service:"
echo "   ./setup-tunnel-service.sh my-app     # Create systemd service"
echo "   sudo systemctl start heritage-tunnel # Start service"
echo ""
echo "📝 Notes:"
echo "   - First connection requires clicking a confirmation link"
echo "   - The tunnel runs as long as this script is active"
echo "   - Press Ctrl+C to stop the tunnel"
echo ""
echo "🎯 For the hackathon demo, run:"
echo "   ./start-https-tunnel.sh heritage-ar26"
echo ""

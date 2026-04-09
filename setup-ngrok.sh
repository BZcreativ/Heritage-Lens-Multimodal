#!/bin/bash
# Setup ngrok for Heritage Lens HTTPS tunnel

echo "=========================================="
echo "ngrok HTTPS Tunnel Setup"
echo "=========================================="
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found. Installing..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update && sudo apt install -y ngrok
fi

echo "✅ ngrok installed: $(ngrok version)"
echo ""

# Check if authtoken is configured
if ! ngrok config check 2>/dev/null | grep -q "valid"; then
    echo "⚠️  ngrok requires an authtoken"
    echo ""
    echo "Setup steps:"
    echo "1. Sign up for free at: https://dashboard.ngrok.com/signup"
    echo "2. Get your authtoken: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "3. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    echo "Or run this command with your token:"
    echo "   ngrok config add-authtoken <your-token>"
    echo ""
    exit 1
fi

echo "✅ ngrok authtoken configured"
echo ""

# Create start script
cat > ~/start-ngrok.sh << 'EOF'
#!/bin/bash
# Start ngrok HTTPS tunnel for Heritage Lens

echo "🚀 Starting ngrok HTTPS tunnel..."
echo "   Local: http://localhost:8501"
echo ""
echo "Your HTTPS URL will appear below (look for 'Forwarding'):"
echo "=========================================="
ngrok http 8501 --bind-tls=true
EOF

chmod +x ~/start-ngrok.sh

echo "🎉 Setup complete!"
echo ""
echo "To start the tunnel, run:"
echo "   ./start-ngrok.sh"
echo ""
echo "ngrok will display your HTTPS URL. Look for:"
echo "   Forwarding: https://xxxx-xx-xx-xxx-xx.ngrok-free.app -> http://localhost:8501"
echo ""

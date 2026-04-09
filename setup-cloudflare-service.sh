#!/bin/bash
# Setup systemd service for persistent Cloudflare Tunnel
# This creates a service that auto-starts on boot and restarts on failure

set -e

SERVICE_NAME="heritage-cloudflare"

echo "=========================================="
echo "Cloudflare Tunnel Systemd Service Setup"
echo "=========================================="
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared not found. Run ./setup-cloudflare-tunnel.sh first"
    exit 1
fi

echo "✅ cloudflared found"
echo ""

# Create systemd service file
cat > /etc/systemd/system/${SERVICE_NAME}.service << 'EOF'
[Unit]
Description=Heritage Lens Cloudflare Tunnel
After=network-online.target docker.service
Wants=network-online.target
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/heritage
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:8501
Restart=always
RestartSec=10
StandardOutput=append:/var/log/cloudflare-tunnel.log
StandardError=append:/var/log/cloudflare-tunnel.log

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Systemd service file created"
echo ""

# Reload systemd
systemctl daemon-reload

echo "✅ Systemd daemon reloaded"
echo ""

# Enable service to start on boot
systemctl enable ${SERVICE_NAME}.service

echo "=========================================="
echo "✅ Service Setup Complete!"
echo "=========================================="
echo ""
echo "Commands:"
echo "  sudo systemctl start ${SERVICE_NAME}    # Start tunnel now"
echo "  sudo systemctl stop ${SERVICE_NAME}     # Stop tunnel"
echo "  sudo systemctl restart ${SERVICE_NAME}  # Restart tunnel"
echo "  sudo systemctl status ${SERVICE_NAME}   # Check status"
echo "  sudo journalctl -u ${SERVICE_NAME} -f   # View logs"
echo ""
echo "🌐 Your HTTPS URL will be in the logs:"
echo "   sudo journalctl -u ${SERVICE_NAME} | grep 'trycloudflare.com'"
echo ""
echo "📝 Logs are also saved to: /var/log/cloudflare-tunnel.log"
echo ""
echo "🚀 To start the tunnel now:"
echo "   sudo systemctl start ${SERVICE_NAME}"
echo ""

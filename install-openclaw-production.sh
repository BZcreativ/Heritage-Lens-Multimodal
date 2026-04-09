#!/bin/bash
# OpenClaw Production Installation Script
# HeritageLens Bot Setup

set -e

# Configuration
USER_NAME="heritage"
USER_HOME="/home/$USER_NAME"
OPENCLAW_PORT="18789"
SLACK_BOT_TOKEN="xoxb-YOUR-BOT-TOKEN-HERE"
SLACK_APP_TOKEN="xapp-YOUR-APP-TOKEN-HERE"
SLACK_CHANNEL_ID="C0AQTGJNVMH"

# Auto-Reply Settings
# Set to "true" to respond to ALL messages (not just @mentions)
AUTO_REPLY="false"

echo "==================================="
echo "OpenClaw Production Installation"
echo "==================================="

# Step 1: Create user if doesn't exist
if ! id "$USER_NAME" &>/dev/null; then
    echo "Creating user: $USER_NAME"
    useradd -m -s /bin/bash "$USER_NAME"
fi

# Step 2: Install fnm (Fast Node Manager)
echo "Installing fnm..."
curl -fsSL https://github.com/Schniz/fnm/releases/latest/download/fnm-linux.zip -o /tmp/fnm-linux.zip
unzip -o /tmp/fnm-linux.zip -d "$USER_HOME/.local/bin/"
chmod +x "$USER_HOME/.local/bin/fnm"
chown -R "$USER_NAME:$USER_NAME" "$USER_HOME/.local"

# Step 3: Install Node.js
echo "Installing Node.js 22..."
su - "$USER_NAME" -c '
    export FNM_DIR="$HOME/.local/share/fnm"
    export PATH="$HOME/.local/bin:$PATH"
    eval "$(fnm env)"
    fnm install 22
    fnm default 22
    fnm use 22
'

# Step 4: Add fnm to user's .bashrc
if ! grep -q 'FNM_DIR' "$USER_HOME/.bashrc"; then
    cat >> "$USER_HOME/.bashrc" << 'EOF'

# fnm - Fast Node Manager
export FNM_DIR="$HOME/.local/share/fnm"
export PATH="$HOME/.local/bin:$PATH"
eval "$(fnm env 2>/dev/null || true)"
EOF
fi
chown "$USER_NAME:$USER_NAME" "$USER_HOME/.bashrc"

# Step 5: Install OpenClaw
echo "Installing OpenClaw..."
su - "$USER_NAME" -c '
    export FNM_DIR="$HOME/.local/share/fnm"
    export PATH="$HOME/.local/bin:$PATH"
    eval "$(fnm env)"
    npm install -g openclaw
'

# Step 6: Create OpenClaw wrapper
cat > /usr/local/bin/openclaw << EOF
#!/bin/bash
# OpenClaw wrapper - uses $USER_NAME user's fnm installation

HERITAGE_HOME="$USER_HOME"
export PATH="$HERITAGE_HOME/.local/share/fnm/node-versions/v22.22.2/installation/bin:\$PATH"
export FNM_DIR="$HERITAGE_HOME/.local/share/fnm"

NODE_PATH="$HERITAGE_HOME/.local/share/fnm/node-versions/v22.22.2/installation/bin/node"
OPENCLAW_PATH="$HERITAGE_HOME/.local/share/fnm/node-versions/v22.22.2/installation/lib/node_modules/openclaw/openclaw.mjs"

if [ ! -x "\$NODE_PATH" ]; then
    echo "Error: Node.js not found" >&2
    exit 1
fi

exec "\$NODE_PATH" "\$OPENCLAW_PATH" "\$@"
EOF
chmod +x /usr/local/bin/openclaw

# Step 7: Initialize OpenClaw
echo "Initializing OpenClaw..."
su - "$USER_NAME" -c '
    export FNM_DIR="$HOME/.local/share/fnm"
    export PATH="$HOME/.local/bin:$PATH"
    eval "$(fnm env)"
    openclaw setup
'

# Step 8: Configure OpenClaw for Slack
echo "Configuring Slack integration..."
su - "$USER_NAME" -c "
    export FNM_DIR=\"\$HOME/.local/share/fnm\"
    export PATH=\"\$HOME/.local/bin:\$PATH\"
    eval \"\$(fnm env)\"

    # Configure Slack channel
    openclaw config set channels.slack.enabled true
    openclaw config set channels.slack.botToken '$SLACK_BOT_TOKEN'
    openclaw config set channels.slack.appToken '$SLACK_APP_TOKEN'
    openclaw config set channels.slack.groupPolicy allowlist
    openclaw config set channels.slack.mode socket
    openclaw config set channels.slack.streaming block
    openclaw config set channels.slack.capabilities.interactiveReplies true
    openclaw config set channels.slack.channels.$SLACK_CHANNEL_ID.enabled true

    # Configure auto-reply (respond to all messages, not just @mentions)
    if [ "$AUTO_REPLY" = "true" ]; then
        echo "Enabling auto-reply for all messages..."
        openclaw config set "channels.slack.channels.$SLACK_CHANNEL_ID.requireMention" false
        openclaw config set channels.slack.replyToMode all
        openclaw config set channels.slack.groupPolicy open
    fi
"

# Step 9: Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/openclaw-gateway.service << EOF
[Unit]
Description=OpenClaw Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$USER_HOME
Environment="FNM_DIR=$USER_HOME/.local/share/fnm"
Environment="PATH=$USER_HOME/.local/share/fnm/node-versions/v22.22.2/installation/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$USER_HOME/.local/share/fnm/node-versions/v22.22.2/installation/bin/node $USER_HOME/.local/share/fnm/node-versions/v22.22.2/installation/lib/node_modules/openclaw/openclaw.mjs gateway --bind loopback --port $OPENCLAW_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Step 10: Configure firewall (optional)
if command -v ufw &> /dev/null; then
    echo "Configuring firewall..."
    ufw allow 22/tcp
    ufw allow $OPENCLAW_PORT/tcp
    ufw --force enable
fi

# Step 11: Start OpenClaw Gateway
echo "Starting OpenClaw Gateway..."
systemctl daemon-reload
systemctl enable openclaw-gateway.service
systemctl start openclaw-gateway.service

sleep 3

# Step 12: Verify installation
echo ""
echo "==================================="
echo "Installation Complete!"
echo "==================================="
echo ""
echo "Gateway Status: $(systemctl is-active openclaw-gateway.service)"
echo ""
echo "Check logs: journalctl -u openclaw-gateway.service -f"
echo "Check status: su - $USER_NAME -c 'openclaw status'"
echo ""
echo "Slack Bot Setup:"
echo "- Bot is configured for channel: $SLACK_CHANNEL_ID"
echo "- Socket Mode: Enabled"
echo "- Streaming: Block mode (clean output)"
echo "- Auto-Reply: $AUTO_REPLY (respond to all messages: $AUTO_REPLY)"
echo ""
if [ "$AUTO_REPLY" = "true" ]; then
    echo "NOTE: Auto-reply is enabled. The bot will respond to ALL messages."
    echo "      Make sure 'message.channels' event is enabled in Slack app."
    echo ""
fi
echo "IMPORTANT: Make sure your Slack app has these scopes:"
echo "  - app_mentions:read"
echo "  - chat:write"
echo "  - channels:history"
echo "  - im:history"
echo "  - groups:history"
echo ""
echo "And these event subscriptions enabled:"
echo "  - app_mention"
echo "  - message.channels"
echo "  - message.im"
echo ""
if [ "$AUTO_REPLY" = "true" ]; then
    echo "For auto-reply, you MUST enable:"
    echo "  - message.channels (to receive all channel messages)"
    echo ""
fi

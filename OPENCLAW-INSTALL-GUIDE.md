# OpenClaw Production Installation Guide

Complete step-by-step guide to install OpenClaw with Slack integration on a fresh VPS.

## Prerequisites

- Ubuntu 22.04/24.04 or Debian-based Linux
- Root or sudo access
- Slack app with Bot token and App-Level token
- Domain or IP for the server (optional, for webhook mode)

---

## Option 1: Automated Installation (Recommended)

Download and run the installation script:

```bash
# Download the script
curl -fsSL https://your-server.com/install-openclaw-production.sh -o install-openclaw.sh

# Edit the configuration variables at the top
nano install-openclaw.sh

# Set these variables:
# SLACK_BOT_TOKEN="xoxb-YOUR-BOT-TOKEN"
# SLACK_APP_TOKEN="xapp-YOUR-APP-TOKEN"
# SLACK_CHANNEL_ID="C0AQTGJNVMH"

# Run the script
chmod +x install-openclaw.sh
sudo ./install-openclaw.sh
```

---

## Option 2: Manual Installation

### Step 1: Create a non-root user

```bash
sudo useradd -m -s /bin/bash heritage
sudo usermod -aG sudo heritage
su - heritage
```

### Step 2: Install fnm (Fast Node Manager)

```bash
# Install fnm
curl -fsSL https://github.com/Schniz/fnm/releases/latest/download/fnm-linux.zip -o /tmp/fnm-linux.zip
unzip -o /tmp/fnm-linux.zip -d ~/.local/bin/
chmod +x ~/.local/bin/fnm

# Add to PATH
echo '
# fnm - Fast Node Manager
export FNM_DIR="$HOME/.local/share/fnm"
export PATH="$HOME/.local/bin:$PATH"
eval "$(fnm env 2>/dev/null || true)"
' >> ~/.bashrc

# Reload shell
source ~/.bashrc
```

### Step 3: Install Node.js

```bash
fnm install 22
fnm default 22
fnm use 22

# Verify
node --version  # Should show v22.x.x
```

### Step 4: Install OpenClaw

```bash
npm install -g openclaw

# Create system-wide wrapper (run as root)
sudo tee /usr/local/bin/openclaw << 'EOF'
#!/bin/bash
HERITAGE_HOME="/home/heritage"
export PATH="$HERITAGE_HOME/.local/share/fnm/node-versions/v22.22.2/installation/bin:$PATH"
export FNM_DIR="$HERITAGE_HOME/.local/share/fnm"

NODE_PATH="$HERITAGE_HOME/.local/share/fnm/node-versions/v22.22.2/installation/bin/node"
OPENCLAW_PATH="$HERITAGE_HOME/.local/share/fnm/node-versions/v22.22.2/installation/lib/node_modules/openclaw/openclaw.mjs"

if [ ! -x "$NODE_PATH" ]; then
    echo "Error: Node.js not found" >&2
    exit 1
fi

exec "$NODE_PATH" "$OPENCLAW_PATH" "$@"
EOF
sudo chmod +x /usr/local/bin/openclaw
```

### Step 5: Initialize OpenClaw

```bash
openclaw setup

# This creates:
# - ~/.openclaw/openclaw.json (main config)
# - ~/.openclaw/workspace/ (agent workspace)
# - ~/.openclaw/agents/ (agent configs)
```

### Step 6: Configure Slack Integration

```bash
# Set your tokens (get from Slack app settings)
SLACK_BOT_TOKEN="xoxb-YOUR-BOT-TOKEN-HERE"
SLACK_APP_TOKEN="xapp-YOUR-APP-TOKEN-HERE"
SLACK_CHANNEL_ID="C0AQTGJNVMH"

# Configure Slack in OpenClaw
openclaw config set channels.slack.enabled true
openclaw config set channels.slack.botToken "$SLACK_BOT_TOKEN"
openclaw config set channels.slack.appToken "$SLACK_APP_TOKEN"
openclaw config set channels.slack.mode socket
openclaw config set channels.slack.groupPolicy allowlist
openclaw config set channels.slack.streaming block
openclaw config set channels.slack.capabilities.interactiveReplies true
openclaw config set "channels.slack.channels.$SLACK_CHANNEL_ID.enabled" true
```

#### Auto-Reply Configuration (Respond to all messages)

By default, the bot only responds to @mentions. To make it respond to **all** messages in a channel:

```bash
# Option A: Respond to all messages in a specific channel (no @mention required)
openclaw config set "channels.slack.channels.$SLACK_CHANNEL_ID.requireMention" false
openclaw config set channels.slack.replyToMode all

# Option B: Allow any user to trigger the bot (for groupPolicy)
openclaw config set channels.slack.groupPolicy open
```

| Setting | Value | Description |
|---------|-------|-------------|
| `requireMention` | `false` | Bot responds to all messages, not just @mentions |
| `replyToMode` | `all` | Reply to every message (not just first or batched) |
| `groupPolicy` | `open` | Any user can trigger the bot (not just allowlisted) |

### Step 7: Create systemd Service

```bash
sudo tee /etc/systemd/system/openclaw-gateway.service << 'EOF'
[Unit]
Description=OpenClaw Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=heritage
WorkingDirectory=/home/heritage
Environment="FNM_DIR=/home/heritage/.local/share/fnm"
Environment="PATH=/home/heritage/.local/share/fnm/node-versions/v22.22.2/installation/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/heritage/.local/share/fnm/node-versions/v22.22.2/installation/bin/node /home/heritage/.local/share/fnm/node-versions/v22.22.2/installation/lib/node_modules/openclaw/openclaw.mjs gateway --bind loopback --port 18789
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable openclaw-gateway.service
sudo systemctl start openclaw-gateway.service
```

### Step 8: Configure Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow OpenClaw Gateway (local only)
sudo ufw allow from 127.0.0.1 to any port 18789

# Enable firewall
sudo ufw --force enable
sudo ufw status
```

---

## Slack App Configuration

### Required Bot Token Scopes

In your Slack app settings (api.slack.com/apps):

1. Go to **OAuth & Permissions**
2. Add these **Bot Token Scopes**:
   - `app_mentions:read` - Receive @mentions
   - `chat:write` - Send messages
   - `channels:history` - Read channel messages
   - `im:history` - Read DM messages
   - `groups:history` - Read private channel messages
   - `channels:read` - Get channel info

3. **Reinstall to Workspace** after adding scopes

### Enable Socket Mode

1. Go to **Socket Mode** in the left sidebar
2. Toggle **Enable Socket Mode** to ON
3. Generate an **App-Level Token** with `connections:write` scope
4. Copy the token (starts with `xapp-`)

### Subscribe to Events

1. Go to **Event Subscriptions**
2. Toggle **Enable Events** to ON
3. Add these **Bot Events**:
   - `app_mention` - When bot is @mentioned
   - `message.channels` - Messages in channels
   - `message.im` - Direct messages

---

## Verification

### Check Gateway Status

```bash
# Check service status
sudo systemctl status openclaw-gateway.service

# Check logs
sudo journalctl -u openclaw-gateway.service -f

# Check OpenClaw status
openclaw status
```

### Test in Slack

1. Invite bot to channel: `/invite @heritagelens`
2. **With @mention**: `@heritagelens hello!`
3. **Without @mention** (if auto-reply enabled): Just type `hello bot`
4. Or send a **DM** to the bot directly

> **Note:** If the bot only responds to @mentions, see [Auto-Reply Configuration](#auto-reply-configuration) above to enable responses to all messages.

---

## Troubleshooting

### Gateway won't start

```bash
# Check logs
sudo journalctl -u openclaw-gateway.service -n 50 --no-pager

# Check port conflict
sudo ss -tlnp | grep 18789

# Fix permissions
sudo chown -R heritage:heritage /home/heritage/.openclaw/
```

### Bot not responding in Slack

1. **Check Socket Mode is enabled** in Slack app settings
2. **Verify tokens** are correct in OpenClaw config
3. **Check scopes** are added and app is reinstalled
4. **Invite bot to channel**: `/invite @heritagelens`
5. **Check event subscriptions** are enabled

### Bot only responds to @mentions, not all messages

The bot defaults to requiring @mentions. To respond to all messages:

```bash
# Enable auto-reply for all messages in channel
openclaw config set "channels.slack.channels.CHANNEL_ID.requireMention" false
openclaw config set channels.slack.replyToMode all
sudo systemctl restart openclaw-gateway.service
```

Also verify in Slack app settings:
- **Event Subscriptions** → Subscribe to `message.channels` bot event

### Tool calls showing in Slack

```bash
# Set streaming to block mode
openclaw config set channels.slack.streaming block
sudo systemctl restart openclaw-gateway.service
```

---

## Management Commands

```bash
# Restart gateway
sudo systemctl restart openclaw-gateway.service

# Stop gateway
sudo systemctl stop openclaw-gateway.service

# View logs
sudo journalctl -u openclaw-gateway.service -f

# OpenClaw TUI
openclaw tui

# Check status
openclaw status

# Run doctor
openclaw doctor --repair
```

---

## Files and Locations

| File/Directory | Purpose |
|----------------|---------|
| `/home/heritage/.openclaw/openclaw.json` | Main configuration |
| `/home/heritage/.openclaw/workspace/` | Agent workspace |
| `/home/heritage/.openclaw/agents/` | Agent configurations |
| `/etc/systemd/system/openclaw-gateway.service` | Systemd service file |
| `/tmp/openclaw-*/` | Log files |

---

## Security Notes

- Gateway runs on localhost only (`--bind loopback`)
- Token auth is enabled by default
- Consider disabling `controlUi.allowInsecureAuth` for production
- Use environment variables or secrets management for tokens

---

## Next Steps

- Configure memory search (optional): Set up OpenAI/Google API key
- Add more channels to the allowlist
- Set up monitoring/alerting for the gateway
- Configure backup for `.openclaw/` directory

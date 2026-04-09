#!/bin/bash
# Setup script for OpenClaw agents
# This recreates the agent configuration from the safe GitHub export

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.openclaw/agents"

echo "=========================================="
echo "OpenClaw Agents Setup"
echo "=========================================="
echo ""

# Check if running from the right directory
if [ ! -f "$SCRIPT_DIR/README.md" ]; then
    echo "❌ Error: Please run this script from the agents-safe-for-github directory"
    exit 1
fi

# Create target directory
mkdir -p "$TARGET_DIR"

echo "📁 Target directory: $TARGET_DIR"
echo ""

# Copy agent configurations
for agent in heritage-lens-multimodal heritage-lens main; do
    if [ -d "$SCRIPT_DIR/$agent" ]; then
        echo "Setting up agent: $agent"

        # Create agent directory
        mkdir -p "$TARGET_DIR/$agent/agent"
        mkdir -p "$TARGET_DIR/$agent/sessions"

        # Copy markdown files
        if [ -d "$SCRIPT_DIR/$agent/agent" ]; then
            cp -r "$SCRIPT_DIR/$agent/agent/"*.md "$TARGET_DIR/$agent/agent/" 2>/dev/null || true
        fi

        # Check for models.json
        if [ ! -f "$TARGET_DIR/$agent/agent/models.json" ]; then
            if [ -f "$SCRIPT_DIR/models.json.EXAMPLE" ]; then
                echo "  ⚠️  Creating models.json from template"
                echo "     Please edit: $TARGET_DIR/$agent/agent/models.json"
                cp "$SCRIPT_DIR/models.json.EXAMPLE" "$TARGET_DIR/$agent/agent/models.json"
            fi
        fi

        # Check for auth-profiles.json
        if [ ! -f "$TARGET_DIR/$agent/agent/auth-profiles.json" ]; then
            if [ -f "$SCRIPT_DIR/auth-profiles.json.EXAMPLE" ]; then
                echo "  ⚠️  Creating auth-profiles.json from template"
                cp "$SCRIPT_DIR/auth-profiles.json.EXAMPLE" "$TARGET_DIR/$agent/agent/auth-profiles.json"
            fi
        fi

        echo "  ✅ Done"
    fi
done

echo ""
echo "=========================================="
echo "✅ Agent Setup Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Add your API keys to models.json:"
echo "   ~/.openclaw/agents/heritage-lens-multimodal/agent/models.json"
echo ""
echo "2. Update ~/.openclaw/openclaw.json to include agents:"
echo '   {'
echo '     "agents": {'
echo '       "list": ['
echo '         {'
echo '           "id": "heritage-lens-multimodal",'
echo '           "name": "Heritage Lens Multimodal",'
echo '           "workspace": "/home/heritage/heritage-lens-multimodal",'
echo '           "agentDir": "/home/heritage/.openclaw/agents/heritage-lens-multimodal/agent",'
echo '           "model": "kimi/kimi-code"'
echo '         }'
echo '       ]'
echo '     }'
echo '   }'
echo ""
echo "3. Restart OpenClaw gateway:"
echo "   openclaw gateway restart"
echo ""

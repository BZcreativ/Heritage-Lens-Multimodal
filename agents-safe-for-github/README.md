# OpenClaw Agents - Safe Export for GitHub

This folder contains a sanitized version of the OpenClaw agent configurations for the Heritage Lens project.

## What's Included

This export contains only non-sensitive agent configuration files:
- Agent identity and personality definitions
- Tool descriptions and capabilities
- Bootstrap instructions
- Documentation files

## What's Excluded

The following sensitive files are **NOT** included:
- `models.json` - Contains API keys (KIMI_API_KEY, etc.)
- `auth-profiles.json` - Authentication credentials
- `sessions/` - Conversation history
- `workspace/.openclaw/` - Internal state files
- `workspace/downloads/` - Downloaded files
- `workspace/.git/` - Git repository data

## Agent Structure

Each agent folder contains:

```
agent/
├── AGENTS.md           # Agent definitions and capabilities
├── BOOTSTRAP.md        # Initial agent instructions
├── HEARTBEAT.md        # Health check and status info
├── IDENTITY.md         # Agent identity definition
├── MEMORY.md           # Persistent memory structure
├── SOUL.md            # Core personality and values
├── TOOLS.md           # Available tools and skills
├── USER.md            # User-specific context
├── auth-profiles.json.EXAMPLE  # Auth template (safe to commit)
└── models.json.EXAMPLE         # Models template (safe to commit)
```

## Setup Instructions

To recreate the full agent configuration:

1. Copy this folder to `~/.openclaw/agents/`
2. Create the `sessions/` subdirectory for each agent
3. Add API keys to `models.json` (see template below)
4. Configure `auth-profiles.json` if needed

### Creating models.json

Create `agent/models.json` in each agent folder:

```json
{
  "providers": {
    "kimi": {
      "baseUrl": "https://api.kimi.com/coding/",
      "api": "anthropic-messages",
      "headers": {
        "User-Agent": "claude-code/0.1.0"
      },
      "models": [
        {
          "id": "kimi-code",
          "name": "Kimi Code",
          "api": "anthropic-messages",
          "reasoning": true,
          "input": ["text", "image"],
          "cost": {
            "input": 0,
            "output": 0,
            "cacheRead": 0,
            "cacheWrite": 0
          },
          "contextWindow": 262144,
          "maxTokens": 32768
        }
      ],
      "apiKey": "YOUR_KIMI_API_KEY_HERE"
    }
  }
}
```

**Never commit the actual models.json with real API keys!**

## Agents

### heritage-lens-multimodal

The main Heritage Lens multimodal agent for cultural heritage exploration.

**Capabilities:**
- Text retrieval from indexed documents
- Image retrieval via CLIP embeddings
- Multimodal synthesis with image context
- Epistemic transparency analysis
- 3-layer output generation

**Workspace:** `/home/heritage/heritage-lens-multimodal`

### heritage-lens

Legacy Heritage Lens agent (single agent mode).

**Workspace:** `~/.openclaw/agents/heritage-lens/workspace`

### main

Default OpenClaw agent for general use.

**Workspace:** `~/.openclaw/workspace`

## Security Notes

- This export contains NO API keys or credentials
- All secrets must be added locally after cloning
- Use environment variables for secrets when possible
- Add `models.json` and `auth-profiles.json` to `.gitignore`

## License

Part of the Heritage Lens project for KXSB AR26 Hackathon.

# OpenClaw Integration Guide

This guide explains how to integrate the Heritage Lens Multimodal system with OpenClaw gateway.

## Overview

There are three ways to integrate with OpenClaw:

1. **Direct Bridge** (Recommended) - Use the Python bridge module
2. **HTTP API** - Expose via FastAPI endpoints
3. **OpenClaw Agent Binding** - Route queries through OpenClaw agent system

## Method 1: Direct Bridge (Recommended)

The bridge module provides seamless integration with OpenClaw.

### Quick Start

```python
from agents.openclaw_integration import OpenClawMultimodalBridge

# Initialize bridge
bridge = OpenClawMultimodalBridge()

# Process query
result = await bridge.handle_query(
    query="What are Olmec colossal heads?",
    session_id="user_123",
    context={"top_k_text": 5, "top_k_images": 3}
)

# Access response
print(result["response"])  # Layer 1: Answer
print(result["metadata"]["layers"]["l2_attribution"])  # Sources
print(result["metadata"]["images"])  # Retrieved images
```

### Response Format

The bridge returns a standardized response:

```json
{
  "response": "Human-readable answer with image references",
  "metadata": {
    "system": "heritage-lens-multimodal",
    "layers": {
      "l1_answer": "...",
      "l2_attribution": {...},
      "l3_epistemic": {...}
    },
    "retrieval_stats": {
      "text_retrieved": 5,
      "images_retrieved": 3
    },
    "critique": {
      "verdict": "accept",
      "confidence": 0.85
    },
    "images": [
      {"path": "...", "caption": "...", "similarity": 0.92}
    ]
  }
}
```

## Method 2: HTTP API

Expose the multimodal system via FastAPI for OpenClaw to call.

### Start API Server

```bash
# Install dependencies
pip install fastapi uvicorn

# Start server
python -c "
from agents.openclaw_integration import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
"
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/query` | POST | Submit query |

### Example Request

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are Olmec colossal heads?",
    "session_id": "user_123",
    "context": {"top_k_text": 5, "top_k_images": 3}
  }'
```

## Method 3: OpenClaw Agent Binding

Route Slack messages through the multimodal agent.

### Step 1: Update OpenClaw Configuration

Add to `~/.openclaw/openclaw.json`:

```json
{
  "agents": {
    "list": [
      {
        "id": "heritage-lens-multimodal",
        "name": "Heritage Lens Multimodal",
        "workspace": "/home/heritage/heritage-lens-multimodal",
        "agentDir": "/home/heritage/.openclaw/agents/heritage-lens-multimodal",
        "model": "kimi/kimi-code",
        "capabilities": [
          "text_retrieval",
          "image_retrieval",
          "multimodal_synthesis",
          "epistemic_analysis"
        ]
      }
    ]
  },
  "bindings": [
    {
      "type": "route",
      "agentId": "heritage-lens-multimodal",
      "match": {
        "channel": "slack",
        "accountId": "default"
      }
    }
  ]
}
```

### Step 2: Create Agent Bootstrap

Create `~/.openclaw/agents/heritage-lens-multimodal/agent/bootstrap.md`:

```markdown
# Heritage Lens Multimodal Agent

You are the Heritage Lens Multimodal orchestrator. Your role is to:

1. **Process Queries**: Use the multimodal bridge to handle cultural heritage queries
2. **3-Layer Output**: Always produce answers with source attribution and epistemic transparency
3. **Image Integration**: Reference relevant images when available
4. **Cultural Sensitivity**: Be mindful of cultural context and potential biases

## Available Capabilities

- Text retrieval from indexed documents
- Image retrieval via CLIP embeddings
- Multimodal synthesis with image context
- Epistemic transparency analysis
- 3-layer output generation

## Response Format

Always structure responses as:

### Answer
[Clear, accurate response with image references]

### Sources
[List of text and image sources]

### Confidence & Transparency
[Bias analysis, gaps, and uncertainties]
```

### Step 3: Restart OpenClaw Gateway

```bash
openclaw gateway restart
```

## Testing Integration

### Test Bridge Module

```bash
cd ~/heritage-lens-multimodal
source venv/bin/activate
python test_openclaw_integration.py
```

### Test with Sample Queries

```bash
python demo.py --mode quick
```

## Troubleshooting

### Issue: API Key Errors

**Solution**: Ensure API keys are in `config/.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_API_KEY=sk-...
GLM_API_KEY=...
KIMI_API_KEY=sk-kimi-...
```

**Note**: For OpenClaw TUI, also export to environment:
```bash
export KIMI_API_KEY=$(cat ~/.openclaw/.env | grep KIMI_API_KEY | cut -d= -f2)
```

### Issue: Qdrant Not Found

**Solution**: Start Qdrant:
```bash
docker-compose up -d
curl http://localhost:6333/healthz
```

### Issue: Agent Not Responding

**Solution**: Check OpenClaw gateway status:
```bash
openclaw gateway status
openclaw logs --follow
```

### Issue: No Images Retrieved

**Solution**: Ingest documents with images:
```bash
python -m pipelines.pdf_extraction.multimodal_ingest data/corpus/
```

## Monitoring

Monitor the integration with:

```bash
# Check system health
python verify_setup.py

# Check OpenClaw status
openclaw gateway status

# View logs
openclaw logs --follow

# Test multimodal features
python test_openclaw_integration.py
```

## Advanced Configuration

### Custom Model Settings

Edit `config/settings.yaml`:

```yaml
llm:
  synthesis:
    provider: "openrouter"
    model: "openai/gpt-4o"
    temperature: 0.7
    max_tokens: 2000
```

### Custom Retrieval Settings

```yaml
retrieval:
  text:
    top_k: 5
    similarity_threshold: 0.75
  image:
    top_k: 3
    page_aware_matching: true
    page_tolerance: 2
```

## Public HTTPS Access

For Slack integration to work with external services, you need HTTPS:

### Cloudflare Tunnel (Recommended)

```bash
# Install
./setup-cloudflare-tunnel.sh

# Start temporary URL
./start-cloudflare-tunnel.sh

# Or setup persistent service
./setup-cloudflare-service.sh
sudo systemctl start heritage-cloudflare
```

**Benefits over ngrok:**
- No connection time limits
- No rate limiting
- Custom domains free (with Cloudflare account)

## Support

For issues with:
- **OpenClaw**: Check `~/.openclaw/logs/`
- **Multimodal System**: Run `python verify_setup.py`
- **Integration**: Run `python test_openclaw_integration.py`

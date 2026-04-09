# Heritage Lens Agent

A multimodal AI system for cultural heritage exploration, built for **KXSB AR26 — Mission 4: Ethics, Agency & Societal Impact**.

Combining text and image retrieval with epistemic transparency to provide culturally-aware answers with full attribution.

---

## Overview

Heritage Lens is a sophisticated multimodal AI agent that helps researchers explore cultural heritage documents. It processes both text and images from PDFs, provides answers with source attribution, and includes an epistemic transparency layer that acknowledges what the answer doesn't know.

### Key Features

- **Multimodal Retrieval**: Search across text documents and images simultaneously
- **3-Layer Output**: Answer, Sources, and "What This Answer Doesn't Know" (epistemic transparency)
- **Document Scoping**: Focus queries on specific documents
- **Dark Mode UI**: Modern dark interface with elevated cards and glow effects
- **Archive Management**: Upload, index, scope, and delete documents
- **OpenClaw Integration**: Agent orchestration with Slack connectivity
- **Cloudflare Tunnel**: Free HTTPS public access (no connection limits)

---

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- GitHub account (for OpenClaw integration)

### Installation

```bash
# Clone the repository
git clone https://github.com/BZcreativ/Heritage-Lens-Multimodal.git
cd Heritage-Lens-Multimodal

# Navigate to the main project
cd heritage-lens-multimodal

# Configure API keys
cp config/.env.example config/.env
# Edit config/.env with your API keys

# Start services
docker-compose up -d

# Access the UI
# Local: http://localhost:8501
```

### Public HTTPS Access

```bash
# Install cloudflared
./setup-cloudflare-tunnel.sh

# Start tunnel (temporary URL)
./start-cloudflare-tunnel.sh

# Or setup persistent service
./setup-cloudflare-service.sh
sudo systemctl start heritage-cloudflare
```

---

## Project Structure

```
.
├── heritage-lens-multimodal/    # Main project
│   ├── agents/                  # Multi-agent system
│   │   ├── orchestrator.py      # Main orchestrator
│   │   ├── retrieval/           # Text + image retrieval
│   │   ├── synthesis/           # Answer generation
│   │   ├── epistemic/           # Bias analysis
│   │   ├── critic/              # Quality evaluation
│   │   └── vision/              # CLIP + GLM-4V image analysis
│   ├── ui/
│   │   └── app.py               # Streamlit dashboard
│   ├── config/
│   │   ├── settings.yaml        # System configuration
│   │   └── prompts.yaml         # LLM prompts
│   └── docker-compose.yml       # Services orchestration
│
├── agents-safe-for-github/      # OpenClaw agent configs
│   ├── README.md                # Agent setup guide
│   └── setup-agents.sh          # Agent setup script
│
├── setup-cloudflare-tunnel.sh   # Cloudflare setup
└── README.md                    # This file
```

---

## Architecture

### 5-Agent System

```
User Query → OpenClaw Bridge → EnhancedOrchestrator
                                   │
          ┌──────────┬────────────┼────────────┐
          ↓          ↓            ↓            ↓
    Retrieval   Synthesis    Epistemic    Critic
       Agent       Agent        Agent      Agent
          │          │            │          │
          └──────────┴────────────┴──────────┘
                                   │
                              3-Layer Output
                           (Answer/Sources/Analysis)
```

| Agent | Purpose |
|-------|---------|
| **Retrieval Agent** | Unified text + image retrieval with CLIP embeddings |
| **Vision Agent** | CLIP embeddings + GLM-4V AI image analysis |
| **Synthesis Agent** | Layer 1 (answer) and Layer 2 (attribution) |
| **Epistemic Agent** | Layer 3 (bias, gaps, confidence analysis) |
| **Critic Agent** | Quality evaluation and revision triggers |

### Data Flow

1. **User Query** → Submitted via Streamlit or Slack
2. **Retrieval** → Fetches relevant text and images from Qdrant
3. **Synthesis** → Generates answer with source attribution
4. **Epistemic** → Analyzes bias, gaps, and confidence
5. **Critic** → Evaluates quality and triggers revisions if needed
6. **Output** → 3-column display (Answer / Sources / What This Answer Doesn't Know)

---

## Technologies

| Component | Technology |
|-----------|------------|
| **LLM** | OpenRouter (multi-model), Kimi, OpenAI |
| **Vision** | CLIP-ViT-B-32, GLM-4V |
| **Vector DB** | Qdrant (text + images) |
| **Cache** | Redis |
| **Framework** | LlamaIndex for RAG |
| **UI** | Streamlit (dark mode) |
| **Integration** | OpenClaw (Slack gateway) |
| **Tunnel** | Cloudflare (free, no limits) |

---

## Configuration

### API Keys Required

Edit `heritage-lens-multimodal/config/.env`:

```bash
# OpenRouter (RECOMMENDED - multi-model access)
OPENROUTER_API_KEY=sk-or-v1-...

# Kimi (optional - Moonshot AI)
KIMI_API_KEY=sk-kimi-...

# GLM-4V (optional - enhanced image analysis)
GLM_API_KEY=...
```

See `config/.env.example` for all options.

---

## Using the Interface

### 1. Archive Documents

Upload PDFs, images, or text files:
- Click "📜 Archive Documents" → "Upload to Archive"
- Supports: PDF, PNG, JPG, JPEG, TIFF
- Auto-extracts text and images

### 2. Scope Queries (Optional)

Focus on specific documents:
- Click 🔍 on any indexed document
- Or search across all documents by default

### 3. Ask Questions

Enter your research question at the top:
- Supports any language
- Strict corpus mode: Answers only from your documents
- General mode: Combines corpus with AI knowledge

### 4. Review Results

Three-column layout:
- **THE ANSWER**: Main response with inline images
- **SOURCES**: Text citations and image references
- **WHAT THIS ANSWER DOESN'T KNOW**: Bias analysis, gaps, confidence

---

## OpenClaw Integration

### Setup OpenClaw Agents

```bash
# Copy safe agents to OpenClaw
cd agents-safe-for-github
./setup-agents.sh

# Add your API keys
vim ~/.openclaw/agents/heritage-lens-multimodal/agent/models.json

# Restart OpenClaw gateway
openclaw gateway restart
```

### Slack Integration

The agent can respond to Slack messages:
- Direct messages
- Channel mentions
- Thread replies

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `setup-cloudflare-tunnel.sh` | Install cloudflared |
| `start-cloudflare-tunnel.sh` | Start HTTPS tunnel |
| `setup-cloudflare-service.sh` | Create systemd service |
| `quickstart.sh` | One-command project setup |
| `verify_setup.py` | Configuration checker |

---

## Health Check

Check system status:

```bash
# Cloudflare tunnel
sudo systemctl status heritage-cloudflare

# Docker services
docker-compose ps

# OpenClaw gateway
openclaw gateway status

# Qdrant
curl http://localhost:6333/healthz
```

---

## Security

- **No credentials in git**: `.gitignore` excludes all `.env` files
- **API keys in environment**: Loaded from `config/.env` (git-ignored)
- **Local-only services**: Qdrant, Redis bind to localhost
- **Document isolation**: Scoped queries limit data exposure

---

## Documentation

| Document | Description |
|----------|-------------|
| [heritage-lens-multimodal/README.md](heritage-lens-multimodal/README.md) | Detailed project guide |
| [heritage-lens-multimodal/README_ARCHITECTURE.md](heritage-lens-multimodal/README_ARCHITECTURE.md) | System architecture |
| [heritage-lens-multimodal/OPENCLAW_INTEGRATION.md](heritage-lens-multimodal/OPENCLAW_INTEGRATION.md) | OpenClaw setup |
| [heritage-lens-multimodal/CHANGELOG.md](heritage-lens-multimodal/CHANGELOG.md) | Version history |
| [agents-safe-for-github/README.md](agents-safe-for-github/README.md) | Agent configuration |

---

## Current Status

**Last Updated:** April 9, 2026

| Service | Status |
|---------|--------|
| Cloudflare Tunnel | ✅ Active |
| Streamlit UI | ✅ OK (port 8501) |
| Qdrant Vector DB | ✅ Green (358 text + 128 image points) |
| Redis Cache | ✅ OK |
| OpenClaw Gateway | ✅ Live (port 18789) |
| Slack Integration | ✅ Connected |

---

## License

Built for **KXSB AR26 Hackathon — Mission 4: Ethics, Agency & Societal Impact**.

---

*For support, see the [troubleshooting guide](heritage-lens-multimodal/README.md#troubleshooting).*

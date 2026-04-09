# Heritage Lens Agent

A multimodal AI system for cultural heritage exploration, built for **KXSB AR26 — Mission 4: Ethics, Agency & Societal Impact**.

Combining text and image retrieval with epistemic transparency to provide culturally-aware answers with full attribution.

> 📖 **Architecture Documentation**: See [README_ARCHITECTURE.md](README_ARCHITECTURE.md) for detailed system architecture, data flows, and agent responsibilities.
> 🤖 **OpenClaw Integration**: See [OPENCLAW_INTEGRATION.md](OPENCLAW_INTEGRATION.md) for gateway integration details.

---

## Features

- **Multimodal Retrieval**: Search across text documents and images simultaneously
- **3-Layer Output**: Answer, Sources, and "What This Answer Doesn't Know" (epistemic transparency)
- **Document Scoping**: Focus queries on specific documents
- **Dark Mode UI**: Modern dark interface with sky blue accents
- **Archive Management**: Upload, index, scope, and delete documents
- **Metadata Preview**: Inspect document details with one click
- **OpenClaw Integration**: Agent orchestration with fallback support

---

## Quick Start

### Using Docker Compose (Recommended)

```bash
cd ~/heritage-lens-multimodal

# Start all services
docker-compose up -d

# Access Streamlit UI
# Local: http://localhost:8501
```

### Public HTTPS Access (Cloudflare Tunnel)

For public access without ngrok connection limits:

```bash
# 1. Install cloudflared (one-time)
./setup-cloudflare-tunnel.sh

# 2. Start tunnel
./start-cloudflare-tunnel.sh

# Output: https://random-words.trycloudflare.com
```

**For persistent tunnel** (auto-start on boot):
```bash
./setup-cloudflare-service.sh
sudo systemctl start heritage-cloudflare
```

### Manual Setup

```bash
cd ~/heritage-lens-multimodal
bash quickstart.sh
```

Or step by step:

```bash
# 1. Setup Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure API Keys
cp config/.env.example config/.env
# Edit config/.env with your API keys

# 3. Start Qdrant
docker-compose up -d qdrant

# 4. Launch UI
streamlit run ui/app.py
```

---

## Configuration

### API Keys

Copy the template and add your keys:

```bash
cp config/.env.example config/.env
```

**Required (one of):**
- `OPENROUTER_API_KEY` - Recommended, access multiple models via [openrouter.ai](https://openrouter.ai)
- `OPENAI_API_KEY` - Direct OpenAI access

**Optional (enhanced capabilities):**
- `GLM_API_KEY` - AI-powered image analysis via [z.ai](https://z.ai)
- `KIMI_API_KEY` - Moonshot AI models
- `ANTHROPIC_API_KEY` - Claude models
- `GOOGLE_API_KEY` - Gemini models

### Settings

Key settings in `config/settings.yaml`:

```yaml
retrieval:
  text:
    top_k: 5
    similarity_threshold: 0.75
  image:
    top_k: 3
    similarity_threshold: 0.7
    page_aware_matching: false

llm:
  synthesis:
    provider: "openrouter"
    model: "openai/gpt-4o"
```

---

## Using the Interface

### 1. Archive Documents

Upload PDFs, images, or text files to the knowledge base:
- Click "Upload to Archive"
- Select files (PDF, PNG, JPG, TIFF supported)
- Documents auto-index with text + image extraction

### 2. Scope Queries (Optional)

Focus on specific documents:
- Click the 🔍 button on any indexed document
- Or search across all documents by default

### 3. Ask Questions

Enter your research question at the top:
- Supports any language
- Strict corpus mode: Answers only from your documents
- General mode: Combines corpus with AI knowledge

### 4. Review Results

Three-column layout shows:
- **THE ANSWER**: Main response with inline images
- **SOURCES**: Text citations and image references
- **WHAT THIS ANSWER DOESN'T KNOW**: Bias analysis, gaps, confidence

### 5. Manage Archive

- **Filter**: All, PDF, Image, Text
- **Search**: Filter by filename
- **Delete**: Select documents and click "🗑️ Delete"
- **Metadata**: Click ℹ️ for document details

---

## Project Structure

```
heritage-lens-multimodal/
├── agents/                     # Multi-agent system
│   ├── orchestrator.py         # EnhancedOrchestrator
│   ├── openclaw_integration.py # OpenClaw bridge
│   ├── retrieval/              # Text + image retrieval
│   ├── synthesis/              # Answer generation
│   ├── epistemic/              # Bias analysis
│   ├── critic/                 # Quality evaluation
│   └── vision/                 # CLIP + GLM-4V image analysis
├── pipelines/
│   └── pdf_extraction/
│       └── multimodal_ingest.py # PDF processing
├── ui/
│   └── app.py                  # Streamlit dashboard (dark mode)
├── utils/
│   └── document_registry.py    # SQLite document tracking
├── config/
│   ├── settings.yaml           # System configuration
│   ├── prompts.yaml            # LLM prompts
│   └── .env.example            # API key template
├── data/
│   ├── corpus/                 # Uploaded documents
│   ├── extracted_images/       # PDF image extractions
│   └── text_chunks/            # Processed text segments
├── docker-compose.yml          # Qdrant + Redis + Streamlit
├── quickstart.sh               # One-command setup
└── verify_setup.py             # Configuration checker
```

---

## Architecture

### Sub-Agents

| Agent | Purpose | Location |
|-------|---------|----------|
| **Retrieval Agent** | Unified text + image retrieval | `agents/retrieval/` |
| **Vision Agent** | CLIP embeddings, GLM-4V analysis | `agents/vision/` |
| **Synthesis Agent** | Layer 1/2 generation | `agents/synthesis/` |
| **Epistemic Agent** | Layer 3 bias/gap analysis | `agents/epistemic/` |
| **Critic Agent** | Quality evaluation | `agents/critic/` |
| **Orchestrator** | Coordinates all agents | `agents/orchestrator.py` |

### Data Flow

```
User Query → OpenClaw Bridge → Orchestrator
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
               Retrieval      Synthesis       Epistemic
                    ↓               ↓               ↓
               Qdrant Text    Layer 1/2         Layer 3
               Qdrant Images  (Answer/Sources)  (Analysis)
```

### Storage

| Type | Technology | Collection |
|------|------------|------------|
| Text | Qdrant + sentence-transformers | `heritage_lens_text` |
| Images | Qdrant + CLIP | `heritage_lens_images` |
| Documents | SQLite | `document_registry.db` |

---

## Vision Capabilities

### Dual Storage System

- **Local Cache** (`embeddings.pkl`): Fast access, ephemeral
- **Qdrant**: Persistent vector database
- **Auto-fallback**: Queries Qdrant when local cache empty

### Modes

**CLIP (Default)**
- Local embedding generation
- No API required
- Basic cultural term matching

**GLM-4V (Enhanced)**
- AI-powered image captioning
- Cultural context analysis
- Requires `GLM_API_KEY`

---

## OpenClaw Integration

### Direct Bridge

```python
from agents.openclaw_integration import OpenClawMultimodalBridge

bridge = OpenClawMultimodalBridge()
result = await bridge.handle_query(
    query="What are Olmec colossal heads?",
    session_id="user_123",
    context={"top_k_text": 5, "top_k_images": 3}
)
```

### HTTP API

```bash
# Start API
uvicorn agents.openclaw_integration:app --host 0.0.0.0 --port 8000

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "...", "session_id": "..."}'
```

---

## Testing

```bash
# Verify setup
python verify_setup.py

# Run all tests
python -m pytest tests/ -v

# Run specific tests
python test_openclaw_integration.py
python demo.py --mode quick
```

---

## Development

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- API keys (see Configuration)

### Adding Features

1. Update relevant agent in `agents/`
2. Add tests in `tests/`
3. Update documentation
4. Run verification: `python verify_setup.py`

---

## Security

- **No credentials in git**: `.gitignore` excludes `config/.env`, keys, databases
- **Local-only services**: Qdrant, Redis bind to localhost
- **API key validation**: Runtime checks for required keys
- **Document isolation**: Scoped queries limit data exposure

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No images retrieved | Check Qdrant: `curl http://localhost:6333/collections/heritage_lens_images` |
| API key errors | Verify `config/.env` has valid keys |
| Qdrant not found | Run `docker-compose up -d qdrant` |
| OpenClaw unavailable | Check `openclaw gateway status` |
| OpenClaw not responding | Export `KIMI_API_KEY` from `.env` file |
| Cloudflare tunnel down | Run `sudo systemctl start heritage-cloudflare` |

---

## Documentation

| Document | Description |
|----------|-------------|
| `README.md` | This file - quick start and usage |
| `README_ARCHITECTURE.md` | System architecture and data flows |
| `OPENCLAW_INTEGRATION.md` | OpenClaw gateway integration |
| `CONTRIBUTING.md` | Development guidelines |
| `CHANGELOG.md` | Version history |

---

## License

Built for KXSB AR26 Hackathon — Mission 4: Ethics, Agency & Societal Impact.

---

*Last updated: April 9, 2026*

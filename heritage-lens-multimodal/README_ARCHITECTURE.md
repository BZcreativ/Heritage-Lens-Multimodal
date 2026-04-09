# Heritage Lens Multimodal - Architecture Documentation

## Overview

Heritage Lens is a multimodal AI agent for cultural heritage exploration. It combines text and image retrieval with epistemic transparency to provide culturally-aware answers with full attribution.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STREAMLIT DASHBOARD                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────────┐  │
│  │   THE ANSWER │  │   SOURCES   │  │   WHAT THIS ANSWER DOESN'T KNOW     │  │
│  │   (Layer 1)  │  │  (Layer 2)  │  │         (Layer 3)                   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OPENCLAW MULTIMODAL BRIDGE                           │
│                    (agents/openclaw_integration.py)                          │
│                                                                              │
│  Routes queries through the multimodal orchestrator with:                    │
│  - Document scoping support                                                  │
│  - Session management                                                        │
│  - Health checks & stats                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ENHANCED ORCHESTRATOR                                   │
│                      (agents/orchestrator.py)                                │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │  RETRIEVAL  │→ │  SYNTHESIS  │→ │  EPISTEMIC  │→ │     CRITIC      │    │
│  │    AGENT    │  │    AGENT    │  │    AGENT    │  │     AGENT       │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘    │
│         │                                                                    │
│    ┌────┴────┐                                                               │
│    ▼         ▼                                                               │
│ ┌──────┐  ┌────────┐                                                         │
│ │ TEXT │  │ IMAGES │                                                         │
│ │Qdrant│  │ Qdrant │                                                         │
│ └──────┘  └────────┘                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agent Responsibilities

### 1. Multimodal Retrieval Agent
**File**: `agents/retrieval/multimodal_retrieval_agent.py`

- **Text Retrieval**: Uses LlamaIndex + Qdrant for semantic text search
- **Image Retrieval**: Uses CLIP embeddings + Qdrant for visual similarity search
- **Document Scoping**: Filters results to specific documents when enabled
- **Page-Aware Matching**: (Currently disabled) Matches images to text based on page proximity

### 2. Multimodal Synthesis Agent
**File**: `agents/synthesis/multimodal_synthesis_agent.py`

- **Layer 1 (Answer)**: Generates the main response with inline citations
- **Layer 2 (Attribution)**: Lists all text and image sources used
- **Strict Corpus Mode**: Enforces answers only from retrieved context

### 3. Enhanced Epistemic Agent
**File**: `agents/epistemic/enhanced_epistemic_agent.py`

- **Layer 3 (Transparency)**: Analyzes biases, gaps, and perspectives
- **Visual Analysis**: Checks for representation biases in images
- **Source Bias Detection**: Identifies colonial vs indigenous perspectives

### 4. Multimodal Critic Agent
**File**: `agents/critic/multimodal_critic_agent.py`

- **Quality Evaluation**: Checks for hallucinations and unsupported claims
- **Revision Strategy**: Determines if re-retrieval is needed
- **Confidence Scoring**: Assigns confidence to the final output

### 5. Vision Agent
**File**: `agents/vision/vision_agent.py`

- **Image Embedding**: CLIP-based vector encoding
- **Image Captioning**: GLM-4V API (with CLIP fallback)
- **Cultural Context Analysis**: Identifies cultural significance
- **Dual Storage**: Local cache (embeddings.pkl) + Qdrant

## Data Storage Architecture

### Text Storage
- **Vector DB**: Qdrant (`heritage_lens_text` collection)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Chunking**: SentenceSplitter (1000 tokens, 200 overlap)

### Image Storage
- **Vector DB**: Qdrant (`heritage_lens_images` collection)
- **Embeddings**: CLIP-ViT-B-32 (512 dimensions)
- **Dual Storage System**:
  ```
  ┌─────────────────────┐     ┌─────────────────────┐
  │   Local Cache       │     │   Qdrant            │
  │   (embeddings.pkl)  │     │   (Vector DB)       │
   │                     │     │                     │
  │  - Fast access      │     │  - Persistent       │
  │  - Lost on restart  │     │  - Cross-container  │
  │  - 255 images       │     │  - 128 images       │
  │  - 358 text chunks  │     │  - 358 text points  │
  └─────────────────────┘     └─────────────────────┘
           ↓                           ↓
           └───────────┬───────────────┘
                       ▼
              ┌─────────────────┐
              │  Vision Agent   │
              │  search_images()│
              └─────────────────┘
  ```

**Important**: The local cache is ephemeral (container restart clears it), but Qdrant persists. The vision agent now queries Qdrant when local cache is empty.

### Document Registry
**File**: `utils/document_registry.py`

SQLite-based tracking for:
- Document upload status
- Indexing state (pending → indexing → indexed → failed)
- Document scoping for focused retrieval

## Data Flow: Image Retrieval

```
User Query: "show me olmec stone heads"
              │
              ▼
┌─────────────────────────────────────┐
│ VisionAgent.search_images()         │
│ 1. Check local cache (empty?)       │
│ 2. If empty → query Qdrant          │
│ 3. Return top-k matches             │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ RetrievalAgent.retrieve()           │
│ - Page-aware matching (disabled)    │
│ - Return images + text              │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ SynthesisAgent.synthesize()         │
│ - Format image context for LLM      │
│ - Include captions & metadata       │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ LLM generates response              │
│ acknowledging images                │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ UI renders in left column           │
│ - render_inline_image()             │
│ - st.image() display                │
└─────────────────────────────────────┘
```

## Configuration Key Points

### Image Retrieval (`config/settings.yaml`)
```yaml
retrieval:
  image:
    top_k: 3
    similarity_threshold: 0.7
    page_aware_matching: false    # Disabled - was filtering valid images
    page_tolerance: 50
```

### Vision Agent
```yaml
vision:
  model: clip-ViT-B-32
  similarity_threshold: 0.75      # For local cache
  # Qdrant uses threshold 0.2 for fallback search
```

### Prompts (`config/prompts.yaml`)
The synthesis prompt explicitly instructs the LLM to acknowledge images:
```yaml
synthesis:
  system: |
    When images are provided in context:
    - ALWAYS acknowledge that images are available
    - Describe what each image shows in detail
```

## Recent Fixes

### 2024-04-07: Image Retrieval from Qdrant
**Problem**: Images indexed in Qdrant (110 images) not being retrieved after container restart.

**Root Cause**: `search_images()` only checked local cache, returned `[]` if empty.

**Solution**: Modified `vision_agent.py` to:
1. First try local cache (fast path)
2. If empty, query Qdrant's `heritage_lens_images` collection
3. Use lower threshold (0.2) for Qdrant CLIP embeddings

### 2024-04-07: Page-Aware Matching Disabled
**Problem**: Images found but filtered out by page-aware matching.

**Root Cause**: Images on pages 58, 85, 105 filtered because text was on different pages (tolerance was 2 pages).

**Solution**: Set `page_aware_matching: false` in settings.yaml

### 2024-04-07: Prompt Enhancement
**Problem**: LLM saying "no images available" even when images retrieved.

**Solution**: Updated prompts to explicitly instruct LLM to acknowledge and describe images.

## API Endpoints (OpenClaw Integration)

The OpenClaw bridge exposes FastAPI endpoints:

```python
POST /query      # Main query endpoint
GET /health      # Health check
GET /            # Root with basic info
```

## Environment Variables

Key variables in `config/.env`:
```bash
# LLM Providers
OPENROUTER_API_KEY=xxx      # Preferred
OPENAI_API_KEY=xxx          # Fallback

# Vector DB
QDRANT_URL=http://qdrant:6333

# Vision
GLM4V_API_KEY=xxx           # For image captioning
```

## Docker Services

```yaml
streamlit:    # UI layer (port 8501)
qdrant:       # Vector database (port 6333/6334)
redis:        # Cache (port 6379)
```

**Note**: OpenClaw runs as a system service (not Docker), see `~/.openclaw/` for configuration.

## Adding New Features

When adding features, update this document with:
1. Architecture diagram changes
2. New agent responsibilities
3. Data flow modifications
4. Configuration options
5. Known limitations

## UI Features

### Dark Mode Interface

The Streamlit dashboard uses a dark theme optimized for research workflows:

```css
Background:        #0d1117 (dark navy)
Card Background:   #161b22 (dark slate)
Accent:            #38bdf8 (sky blue)
Text Primary:      #ffffff
Text Secondary:    #8b949e (muted gray)
```

### Layout

**Header**: "Heritage Lens Agent" + Mission tag (KXSB AR26 — MISSION 4)
**Footer**: OpenClaw connection status with animated indicator
**Main Content**:
- Inquiry input at top
- 3-column results (Answer / Sources / What This Answer Doesn't Know)
- Archive panel with document management

### Archive Panel Features

| Feature | Description |
|---------|-------------|
| Filter | All, PDF, Image, Text |
| Search | Filter by filename |
| Select | Checkbox multi-select |
| Delete | 🗑️ Delete selected documents |
| Scope | 🔍 Focus queries on specific doc |
| Metadata | ℹ️ Preview document details |

---

## Current System Status

**Last updated: 2026-04-09**

| Service | Status | Details |
|---------|--------|---------|
| **Cloudflare Tunnel** | ✅ Active | `https://champagne-employ-dept-declare.trycloudflare.com` |
| **Streamlit UI** | ✅ OK | Port 8501, healthy |
| **Qdrant Vector DB** | ✅ Green | 358 text points, 128 image points |
| **Redis Cache** | ✅ OK | Running |
| **OpenClaw Gateway** | ✅ Live | Port 18789, Slack connected |
| **Disk Space** | ✅ OK | 63% used (81G free) |
| **Memory** | ✅ OK | 4.1G used, 11G available |

### Public Access

The system is accessible via Cloudflare Tunnel:
- **HTTPS URL**: https://champagne-employ-dept-declare.trycloudflare.com
- **Local Access**: http://localhost:8501

### Cloudflare Tunnel Service

For persistent HTTPS access, the tunnel runs as a systemd service:
```bash
sudo systemctl status heritage-cloudflare  # Check status
sudo systemctl start heritage-cloudflare   # Start tunnel
sudo journalctl -u heritage-cloudflare -f  # View logs
```

---

*Last updated: 2026-04-09*

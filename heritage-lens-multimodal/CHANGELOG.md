# Changelog

All notable changes to the Heritage Lens Multimodal project.

## [1.0.1] - 2026-04-09

### Added
- **Cloudflare Tunnel Integration**: Replaced ngrok with Cloudflare Tunnel
  - No connection time limits (vs ngrok 1hr)
  - No rate limiting
  - Auto-start systemd service for persistent HTTPS
  - Scripts: `setup-cloudflare-tunnel.sh`, `start-cloudflare-tunnel.sh`
- **UI Enhancements**:
  - Elevated card styling for "THE ANSWER" and "SOURCES" panels
  - Glowing border effect for "WHAT THIS ANSWER DOESN'T KNOW" panel
  - Fixed deprecated `use_column_width` warning
- **Health Check System**: Comprehensive system status monitoring
  - All services: Cloudflare, Streamlit, Qdrant, Redis, OpenClaw
  - Resource monitoring: disk, memory
  - Vector DB stats: 358 text points, 128 image points

### Fixed
- **OpenClaw API Key Resolution**: Fixed `SecretRef` resolution for Kimi API key
  - Models.json now properly references environment variables
- **HTML Rendering**: Fixed raw HTML display in epistemic panel
  - Converted triple-quoted strings to inline HTML in helper functions
- **Project Root Detection**: Fixed multi-path resolution for Docker/local/OpenClaw environments

### Infrastructure
- **Systemd Services**:
  - `heritage-cloudflare`: Persistent HTTPS tunnel
  - `heritage-streamlit`: Auto-restart Streamlit on boot

## [1.0.0] - 2026-04-06

### Added
- **Multimodal Retrieval System**: Unified text and image retrieval with page-aware matching
- **5 Sub-Agents Architecture**:
  - `MultimodalRetrievalAgent`: LlamaIndex + Qdrant + CLIP integration
  - `VisionAgent`: CLIP embeddings + GLM-4V AI image analysis
  - `MultimodalSynthesisAgent`: Layer 1/2 generation with image context
  - `EnhancedEpistemicAgent`: Layer 3 with visual bias analysis
  - `MultimodalCriticAgent`: Quality evaluation and revision triggers
- **3-Layer Output Format**:
  - Layer 1: Answer with integrated visual context
  - Layer 2: Source attribution (text + images)
  - Layer 3: Epistemic transparency with bias analysis
- **Data Pipeline**: PDF text and image extraction with PyMuPDF
- **Dual UI Options**:
  - Streamlit interface (port 8501)
  - Gradio interface (port 7860)
- **OpenClaw Integration**: Bridge module for gateway connectivity
- **Vision Capabilities**:
  - CLIP similarity search (local)
  - GLM-4V AI captioning (requires API key)
  - Cultural context inference
- **Infrastructure**:
  - Docker Compose for Qdrant + Redis
  - pytest configuration for async testing
  - Environment-based API key management
- **Documentation**:
  - Comprehensive README
  - Interactive demo script
  - Verification script
  - Quick start guide

### Technical Stack
- **LLM**: OpenRouter/OpenAI/Anthropic support
- **Vision**: CLIP-ViT-B-32 + GLM-4V
- **Vector DB**: Qdrant (text) + NumPy cache (images)
- **Framework**: LlamaIndex for RAG
- **UI**: Streamlit + Gradio
- **Testing**: pytest + pytest-asyncio

### Security
- `.gitignore` excludes all `.env` files
- API keys loaded from environment or `.env` file
- No hardcoded credentials in source code

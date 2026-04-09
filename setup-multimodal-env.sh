#!/bin/bash
# Setup multimodal Python environment for Heritage Lens

set -e

echo "==================================="
echo "Setting up Multimodal Python Environment"
echo "==================================="

PROJECT_DIR="$HOME/heritage-lens-multimodal"
cd "$PROJECT_DIR"

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
# Upgrade pip
pip install --upgrade pip

# Install PyTorch (CPU version for VPS)
echo "Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install multimodal RAG packages
echo "Installing multimodal RAG packages..."
pip install llama-index qdrant-client chromadb openai anthropic google-generativeai
pip install streamlit python-dotenv pydantic aiohttp
pip install pandas numpy matplotlib seaborn

# Install PDF and image processing
echo "Installing PDF and image processing..."
pip install pymupdf Pillow sentence-transformers
pip install langchain langchain-community langchain-openai

# Install CLIP and vision models
echo "Installing CLIP and vision models..."
pip install transformers opencv-python-headless scikit-image

# Install sentence-transformers with CLIP support
pip install sentence-transformers[clip]

# Create requirements.txt
echo "Creating requirements.txt..."
pip freeze > requirements.txt

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Activate environment: source ~/heritage-lens-multimodal/venv/bin/activate"
echo "Test CLIP: python -c 'from sentence_transformers import SentenceTransformer; print(\"CLIP ready\")'"

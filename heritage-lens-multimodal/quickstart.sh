#!/bin/bash

# Heritage Lens Multimodal - Quick Start Script
# This script helps you get started quickly with the multimodal system

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           Heritage Lens Multimodal - Quick Start              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if we're in the right directory
if [ ! -f "config/settings.yaml" ]; then
    echo -e "${YELLOW}Error: Please run this script from the heritage-lens-multimodal directory${NC}"
    exit 1
fi

# Step 1: Check virtual environment
echo -e "\n${GREEN}Step 1: Checking virtual environment...${NC}"
if [ -d "venv" ]; then
    echo "✓ Virtual environment found"
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "✗ Virtual environment not found. Running setup..."
    bash setup-multimodal-env.sh
    source venv/bin/activate
fi

# Step 2: Check API keys
echo -e "\n${GREEN}Step 2: Checking API keys...${NC}"
if [ -f "config/.env" ]; then
    echo "✓ config/.env exists"
    # Source the env file to check keys
    export $(grep -v '^#' config/.env | xargs 2>/dev/null || true)

    if [ -n "$OPENROUTER_API_KEY" ] || [ -n "$OPENAI_API_KEY" ]; then
        echo "✓ LLM API key configured"
    else
        echo "✗ No LLM API key found. Please add OPENROUTER_API_KEY or OPENAI_API_KEY to config/.env"
        exit 1
    fi
else
    echo "✗ config/.env not found. Copying from example..."
    cp config/.env.example config/.env
    echo "✗ Please edit config/.env and add your API keys"
    exit 1
fi

# Step 3: Check Qdrant
echo -e "\n${GREEN}Step 3: Checking Qdrant...${NC}"
if curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
    echo "✓ Qdrant is running"
else
    echo "✗ Qdrant not running. Starting..."
    docker-compose up -d
    echo "Waiting for Qdrant to start..."
    sleep 5
    if curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
        echo "✓ Qdrant started successfully"
    else
        echo "✗ Failed to start Qdrant. Please check Docker."
        exit 1
    fi
fi

# Step 4: Run verification
echo -e "\n${GREEN}Step 4: Running verification...${NC}"
python verify_setup.py

# Step 5: Create sample corpus directory
echo -e "\n${GREEN}Step 5: Setting up directories...${NC}"
mkdir -p data/corpus
mkdir -p data/extracted_images
echo "✓ Directories created"

# Final message
echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Quick start complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"

echo -e "\n${BLUE}Next steps:${NC}"
echo ""
echo "1. Add PDF documents to the corpus:"
echo "   cp your_document.pdf data/corpus/"
echo ""
echo "2. Ingest the documents:"
echo "   python -m pipelines.pdf_extraction.multimodal_ingest data/corpus/"
echo ""
echo "3. Run the interactive demo:"
echo "   python demo.py --mode interactive"
echo ""
echo "4. Launch the web UI:"
echo "   streamlit run ui/app.py"
echo "   # or"
echo "   python ui/gradio_app.py"
echo ""
echo "5. Run tests:"
echo "   python -m pytest tests/ -v"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo "  - README.md - Full documentation"
echo "  - demo.py --mode examples - Example queries"
echo ""

#!/bin/bash

# Heritage Lens Multimodal Environment Setup
# Run this script to set up the Python environment

set -e

echo "=============================================="
echo "Heritage Lens Multimodal - Environment Setup"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get project directory
PROJECT_DIR="$HOME/heritage-lens-multimodal"
cd "$PROJECT_DIR"

echo "Project directory: $PROJECT_DIR"

# Check Python version
echo ""
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists${NC}"
    read -p "Recreate? (y/N): " recreate
    if [[ $recreate == "y" || $recreate == "Y" ]]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment recreated${NC}"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch first (CPU version for compatibility)
echo ""
echo "Installing PyTorch (CPU version)..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install other requirements
echo ""
echo "Installing other dependencies..."
pip install -r requirements.txt

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/cache/image_embeddings
mkdir -p data/extracted_images
mkdir -p data/text_chunks
mkdir -p data/chroma
echo -e "${GREEN}✓ Data directories created${NC}"

# Check if .env exists
echo ""
if [ ! -f "config/.env" ]; then
    echo -e "${YELLOW}Warning: config/.env not found${NC}"
    echo "Please copy config/.env.example to config/.env and add your API keys"
    cp config/.env.example config/.env
    echo -e "${GREEN}✓ Created config/.env from template${NC}"
else
    echo -e "${GREEN}✓ config/.env exists${NC}"
fi

# Run test
echo ""
echo "=============================================="
echo "Setup complete!"
echo "=============================================="
echo ""
echo "To activate the environment, run:"
echo "  source $PROJECT_DIR/venv/bin/activate"
echo ""
echo "To test the installation, run:"
echo "  python test_multimodal.py"
echo ""
echo "To launch the UI, run:"
echo "  streamlit run ui/app.py"
echo ""

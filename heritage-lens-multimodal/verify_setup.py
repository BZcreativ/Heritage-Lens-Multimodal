#!/usr/bin/env python3
"""
Quick verification script for Heritage Lens Multimodal setup
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "heritage-lens-multimodal"))

print("=" * 60)
print("Heritage Lens Multimodal - Setup Verification")
print("=" * 60)

# Check imports
print("\n1. Checking imports...")
try:
    from agents.orchestrator import EnhancedOrchestrator
    from agents.vision.vision_agent import VisionAgent
    from agents.retrieval.multimodal_retrieval_agent import MultimodalRetrievalAgent
    from agents.synthesis.multimodal_synthesis_agent import MultimodalSynthesisAgent
    from agents.epistemic.enhanced_epistemic_agent import EnhancedEpistemicAgent
    from agents.critic.multimodal_critic_agent import MultimodalCriticAgent
    from pipelines.pdf_extraction.multimodal_ingest import MultimodalIngestPipeline
    print("   ✓ All imports successful")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Check API keys
print("\n2. Checking API keys...")
import os
env_path = Path.home() / "heritage-lens-multimodal" / "config" / ".env"
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key not in os.environ:
                    os.environ[key] = value

keys = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
    "GLM_API_KEY": os.getenv("GLM_API_KEY"),
    "KIMI_API_KEY": os.getenv("KIMI_API_KEY"),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
}

for key, value in keys.items():
    status = "✓" if value and not value.startswith("xxx") and len(value) > 10 else "✗"
    print(f"   {status} {key}: {bool(value and len(value) > 10)}")

# Check Qdrant
print("\n3. Checking Qdrant connection...")
try:
    from qdrant_client import QdrantClient
    client = QdrantClient(url="http://localhost:6333")
    # Try to get collections
    collections = client.get_collections()
    print(f"   ✓ Qdrant connected ({len(collections.collections)} collections)")
except Exception as e:
    print(f"   ✗ Qdrant not available: {e}")
    print("      Run: docker-compose up -d")

# Check Vision Agent
print("\n4. Checking Vision Agent...")
try:
    vision = VisionAgent()
    stats = vision.get_stats()
    print(f"   ✓ Vision Agent initialized")
    print(f"      - Images indexed: {stats['images_indexed']}")
    print(f"      - GLM enabled: {stats['glm_enabled']}")
    print(f"      - CLIP model: {stats['clip_model']}")
except Exception as e:
    print(f"   ✗ Vision Agent failed: {e}")

# Check Orchestrator
print("\n5. Checking Orchestrator...")
try:
    orch = EnhancedOrchestrator()
    stats = orch.get_stats()
    print(f"   ✓ Orchestrator initialized")
    print(f"      - Sessions: {stats['sessions_active']}")
    print(f"      - Max revisions: {stats['config']['max_revisions']}")
except Exception as e:
    print(f"   ✗ Orchestrator failed: {e}")

print("\n" + "=" * 60)
print("Verification complete!")
print("=" * 60)

print("\nNext steps:")
print("  1. Add PDFs: python -m pipelines.pdf_extraction.multimodal_ingest <pdf>")
print("  2. Run demo: python demo.py --mode quick")
print("  3. Launch UI: streamlit run ui/app.py")

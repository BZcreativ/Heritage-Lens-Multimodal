"""
Tests for Vision Agent
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path.home() / "heritage-lens-multimodal"))

from agents.vision.vision_agent import VisionAgent


@pytest.mark.asyncio
async def test_vision_agent_initialization():
    """Test vision agent initialization and model loading"""
    agent = VisionAgent()

    # Check that model configuration is loaded
    assert hasattr(agent, 'similarity_threshold')
    assert agent.similarity_threshold > 0

    # Check cache directory
    assert Path(agent.cache_dir).exists() or Path(agent.cache_dir).parent.exists()


@pytest.mark.asyncio
async def test_image_search():
    """Test image search functionality"""
    agent = VisionAgent()

    # Test search (may return empty if no images in cache)
    results = await agent.search_images("ancient artifact", top_k=2)

    # Should return list
    assert isinstance(results, list)

    if results:  # If we have images in cache
        for result in results:
            assert "path" in result
            assert "similarity" in result
            assert "metadata" in result
            assert 0 <= result["similarity"] <= 1


@pytest.mark.asyncio
async def test_vision_agent_stats():
    """Test vision agent statistics"""
    agent = VisionAgent()

    # Check initial state
    assert hasattr(agent, 'image_paths')
    assert hasattr(agent, 'image_embeddings')
    assert len(agent.image_paths) == len(agent.image_embeddings) if hasattr(agent.image_embeddings, '__len__') else True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

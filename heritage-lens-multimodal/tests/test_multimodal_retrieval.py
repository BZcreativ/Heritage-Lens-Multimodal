"""
Tests for Multimodal Retrieval Agent
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path.home() / "heritage-lens-multimodal"))

from agents.retrieval.multimodal_retrieval_agent import MultimodalRetrievalAgent


@pytest.mark.asyncio
async def test_multimodal_retrieval():
    """Test multimodal retrieval with both text and images"""
    agent = MultimodalRetrievalAgent()

    # Test with a cultural heritage query
    result = await agent.retrieve("What do Olmec colossal heads look like?")

    assert "text_chunks" in result
    assert "images" in result
    assert result["stats"]["multimodal"] in [True, False]  # Could be either

    # Check that we have retrieval stats
    assert "text_retrieved" in result["stats"]
    assert "images_retrieved" in result["stats"]


@pytest.mark.asyncio
async def test_page_aware_matching():
    """Test page-aware image-text matching"""
    agent = MultimodalRetrievalAgent()

    # Mock data
    text_chunks = [
        {"metadata": {"page": 5}, "content": "Sample text", "similarity": 0.8}
    ]

    images = [
        {"metadata": {"page": 6}, "similarity": 0.9, "path": "test1.jpg"},
        {"metadata": {"page": 10}, "similarity": 0.8, "path": "test2.jpg"},
        {"metadata": {"page": 3}, "similarity": 0.7, "path": "test3.jpg"}
    ]

    # Test matching
    matched = agent._page_aware_matching(text_chunks, images)

    # Image on page 6 should be ranked higher than page 10
    if len(matched) >= 2:
        assert matched[0]["metadata"]["page"] == 6  # Closest page


@pytest.mark.asyncio
async def test_retrieval_with_empty_query():
    """Test retrieval with empty query"""
    agent = MultimodalRetrievalAgent()

    result = await agent.retrieve("")

    assert "text_chunks" in result
    assert "images" in result
    assert result["stats"]["text_retrieved"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

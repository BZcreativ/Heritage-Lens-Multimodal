"""
End-to-End Multimodal Pipeline Test
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path.home() / "heritage-lens-multimodal"))

from agents.orchestrator import EnhancedOrchestrator


@pytest.mark.asyncio
async def test_full_multimodal_pipeline():
    """Test complete multimodal pipeline"""
    orchestrator = EnhancedOrchestrator()

    # Test with a query that should benefit from multimodal context
    result = await orchestrator.process_query("Show me examples of Maya hieroglyphics")

    # Check required fields
    assert "layers" in result
    assert "l1_answer" in result["layers"]  # Answer
    assert "l2_attribution" in result["layers"]  # Sources
    assert "l3_epistemic" in result["layers"]  # Epistemic report
    assert "retrieval" in result
    assert "images" in result["retrieval"]  # Retrieved images
    assert "critique" in result  # Critic verdict

    # Check that verdict is valid
    valid_verdicts = ["accept", "revise_retrieval", "revise_synthesis",
                     "revise_epistemic", "revise_vision"]
    assert result["critique"]["verdict"] in valid_verdicts

    # Check multimodal stats
    assert "stats" in result["retrieval"]
    assert "multimodal" in result["retrieval"]["stats"]

    print(f"✅ Multimodal test passed!")
    print(f"Answer length: {len(result['layers']['l1_answer'])} chars")
    print(f"Images retrieved: {len(result['retrieval']['images'])}")
    print(f"Verdict: {result['critique']['verdict']}")
    print(f"Multimodal coherence: {result['critique'].get('multimodal_coherence', 'N/A')}")


@pytest.mark.asyncio
async def test_orchestrator_with_images():
    """Test orchestrator with image context"""
    orchestrator = EnhancedOrchestrator()

    result = await orchestrator.process_query(
        "What are Olmec colossal heads and show me examples?",
        top_k_text=3,
        top_k_images=2
    )

    assert "layers" in result
    assert result["retrieval"]["stats"]["images_retrieved"] >= 0


@pytest.mark.asyncio
async def test_orchestrator_stats():
    """Test orchestrator statistics"""
    orchestrator = EnhancedOrchestrator()

    stats = orchestrator.get_stats()

    assert "images_indexed" in stats
    assert "sessions_active" in stats
    assert "config" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

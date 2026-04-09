"""
Quick test script for the multimodal agent system
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.append(str(Path.home() / "heritage-lens-multimodal"))

from agents.orchestrator import EnhancedOrchestrator


async def test_basic():
    """Test basic orchestrator functionality"""
    print("=" * 60)
    print("Heritage Lens Multimodal - Basic Test")
    print("=" * 60)

    try:
        # Initialize orchestrator
        print("\n1. Initializing orchestrator...")
        orchestrator = EnhancedOrchestrator()
        print("   ✓ Orchestrator initialized")

        # Check stats
        print("\n2. System stats:")
        stats = orchestrator.get_stats()
        print(f"   - Images indexed: {stats['images_indexed']}")
        print(f"   - Sessions active: {stats['sessions_active']}")
        print(f"   - Max revisions: {stats['config']['max_revisions']}")

        # Test query
        print("\n3. Testing query processing...")
        query = "Tell me about Olmec colossal heads"
        print(f"   Query: '{query}'")

        result = await orchestrator.process_query(query)

        print("\n4. Results:")
        print(f"   - Processing time: {result['processing_time']:.2f}s")
        print(f"   - Text chunks retrieved: {result['retrieval']['stats']['text_retrieved']}")
        print(f"   - Images retrieved: {result['retrieval']['stats']['images_retrieved']}")
        print(f"   - Revisions: {result['revisions']}")

        print("\n5. Layer 1 (Answer preview):")
        answer = result['layers']['l1_answer']
        preview = answer[:300] + "..." if len(answer) > 300 else answer
        print(f"   {preview}")

        print("\n6. Layer 2 (Source Attribution):")
        text_sources = result['layers']['l2_attribution'].get('text_sources', [])
        image_sources = result['layers']['l2_attribution'].get('image_sources', [])
        print(f"   - Text sources: {len(text_sources)}")
        print(f"   - Image sources: {len(image_sources)}")

        print("\n7. Layer 3 (Epistemic):")
        epistemic = result['layers']['l3_epistemic']
        has_textual = bool(epistemic.get('textual_analysis'))
        has_visual = bool(epistemic.get('visual_analysis'))
        has_overall = bool(epistemic.get('overall_assessment'))
        print(f"   - Textual analysis: {'✓' if has_textual else '✗'}")
        print(f"   - Visual analysis: {'✓' if has_visual else '✗'}")
        print(f"   - Overall assessment: {'✓' if has_overall else '✗'}")

        print("\n" + "=" * 60)
        print("✓ Test completed successfully!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_vision_agent():
    """Test vision agent specifically"""
    print("\n" + "=" * 60)
    print("Vision Agent Test")
    print("=" * 60)

    try:
        from agents.vision.vision_agent import VisionAgent

        print("\n1. Initializing vision agent...")
        vision = VisionAgent()
        print("   ✓ Vision agent initialized")

        print(f"\n2. Current image cache:")
        print(f"   - Images indexed: {len(vision.image_paths)}")
        print(f"   - Embeddings shape: {vision.image_embeddings.shape}")
        print(f"   - Cache directory: {vision.cache_dir}")

        print("\n" + "=" * 60)
        print("✓ Vision agent test completed!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ Vision agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nHeritage Lens Multimodal Agent - Test Suite")
    print("Note: This requires the Python environment to be set up.")
    print("Run setup-multimodal-env.sh first if you haven't.\n")

    # Run tests
    success = True

    # Test vision agent
    if not asyncio.run(test_vision_agent()):
        success = False

    # Test basic orchestration
    if not asyncio.run(test_basic()):
        success = False

    print("\n" + "=" * 60)
    if success:
        print("All tests passed!")
    else:
        print("Some tests failed. Check errors above.")
    print("=" * 60)

"""
Test GLM-4V Vision Integration
"""

import sys
import asyncio
from pathlib import Path

sys.path.append(str(Path.home() / "heritage-lens-multimodal"))

from agents.vision.vision_agent import VisionAgent


def test_glm_configuration():
    """Test GLM-4V configuration detection"""
    print("=" * 60)
    print("Testing GLM-4V Configuration")
    print("=" * 60)

    agent = VisionAgent()

    print(f"\nGLM-4V Enabled: {agent.glm_enabled}")

    if agent.glm_enabled:
        print(f"API Key: {agent._glm_api_key[:20]}...")
        print("\n✓ GLM-4V is configured and ready for vision tasks")
    else:
        print("\n⚠ GLM-4V not configured. Add GLM_API_KEY to config/.env")
        print("  Get your key at: https://z.ai/manage-apikey/apikey-list")

    # Show stats
    stats = agent.get_stats()
    print(f"\nVision Agent Stats:")
    print(f"  - Images indexed: {stats['images_indexed']}")
    print(f"  - GLM enabled: {stats['glm_enabled']}")
    print(f"  - CLIP model: {stats['clip_model']}")

    return agent.glm_enabled


async def test_glm_caption_generation():
    """Test GLM-4V caption generation (requires an image)"""
    print("\n" + "=" * 60)
    print("Testing GLM-4V Caption Generation")
    print("=" * 60)

    agent = VisionAgent()

    if not agent.glm_enabled:
        print("\n⚠ Skipping - GLM-4V not configured")
        return False

    # Look for any existing image in cache or create a test
    test_images = list(Path.home().glob("heritage-lens-multimodal/data/extracted_images/*.png"))
    test_images.extend(Path.home().glob("heritage-lens-multimodal/data/extracted_images/*.jpg"))

    if not test_images:
        print("\n⚠ No test images available. Process a PDF first:")
        print("  python -m pipelines.pdf_extraction.multimodal_ingest <pdf_file>")
        return False

    test_image = str(test_images[0])
    print(f"\nTesting with image: {Path(test_image).name}")

    try:
        caption = await agent.generate_caption(test_image)
        print(f"\nGenerated Caption:\n{caption}")
        print("\n✓ GLM-4V caption generation successful!")
        return True
    except Exception as e:
        print(f"\n✗ GLM-4V caption failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_glm_analysis():
    """Test GLM-4V cultural context analysis"""
    print("\n" + "=" * 60)
    print("Testing GLM-4V Cultural Analysis")
    print("=" * 60)

    agent = VisionAgent()

    if not agent.glm_enabled:
        print("\n⚠ Skipping - GLM-4V not configured")
        return False

    test_images = list(Path.home().glob("heritage-lens-multimodal/data/extracted_images/*.png"))

    if not test_images:
        print("\n⚠ No test images available")
        return False

    test_image = str(test_images[0])
    print(f"\nAnalyzing: {Path(test_image).name}")

    try:
        analysis = await agent.analyze_cultural_context(test_image)
        print(f"\nCultural Analysis:")
        print(f"  - Method: {analysis.get('analysis_method', 'unknown')}")
        if 'glm_analysis' in analysis:
            print(f"  - Analysis: {analysis['glm_analysis'][:200]}...")
        print(f"  - Cultural Context: {analysis.get('cultural_context', ['unknown'])}")
        print("\n✓ GLM-4V analysis successful!")
        return True
    except Exception as e:
        print(f"\n✗ GLM-4V analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all GLM tests"""
    print("\nHeritage Lens - GLM-4V Vision Integration Tests")
    print("=" * 60)

    results = []

    # Test configuration
    results.append(("Configuration", test_glm_configuration()))

    # Test caption generation
    results.append(("Caption Generation", await test_glm_caption_generation()))

    # Test cultural analysis
    results.append(("Cultural Analysis", await test_glm_analysis()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\n{passed_count}/{total_count} tests passed")

    return all(p for _, p in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

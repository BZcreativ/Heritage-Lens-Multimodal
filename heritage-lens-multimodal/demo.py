#!/usr/bin/env python3
"""
Heritage Lens Multimodal - Interactive Demo
Demonstrates the 3-layer multimodal output system
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict

sys.path.append(str(Path.home() / "heritage-lens-multimodal"))

from agents.orchestrator import EnhancedOrchestrator


# Example queries for demonstration
EXAMPLE_QUERIES = [
    {
        "category": "Olmec Civilization",
        "queries": [
            "What are Olmec colossal heads and what do they represent?",
            "Describe the artistic style of Olmec jade artifacts",
            "What were the major Olmec archaeological sites?"
        ]
    },
    {
        "category": "Maya Civilization",
        "queries": [
            "Explain Maya hieroglyphic writing system",
            "What is the significance of Maya stelae?",
            "Describe Maya temple-pyramid architecture"
        ]
    },
    {
        "category": "Aztec/Mexica",
        "queries": [
            "What artifacts have been found at the Templo Mayor?",
            "Describe Aztec stone sculpture techniques",
            "What do we know about Aztec ritual objects?"
        ]
    },
    {
        "category": "Comparative Analysis",
        "queries": [
            "Compare Olmec and Maya artistic styles",
            "What are the differences between Mesoamerican ball courts?",
            "How did stone working techniques evolve in Mesoamerica?"
        ]
    }
]


class HeritageLensDemo:
    """Interactive demo for Heritage Lens Multimodal"""

    def __init__(self):
        self.orchestrator = EnhancedOrchestrator()

    async def run_query(self, query: str, show_details: bool = True) -> None:
        """Run a single query and display results"""
        print("\n" + "=" * 80)
        print(f"QUERY: {query}")
        print("=" * 80)

        result = await self.orchestrator.process_query(query)

        # Layer 1: Answer
        print("\n📖 LAYER 1: ANSWER")
        print("-" * 80)
        print(result["layers"]["l1_answer"])

        if show_details:
            # Layer 2: Source Attribution
            print("\n📚 LAYER 2: SOURCE ATTRIBUTION")
            print("-" * 80)
            l2 = result["layers"]["l2_attribution"]

            if l2.get("text_sources"):
                print("\nText Sources:")
                for src in l2["text_sources"][:3]:  # Show top 3
                    print(f"  • {src['reference']} {src['source']}")

            if l2.get("image_sources"):
                print("\nImage Sources:")
                for img in l2["image_sources"][:3]:
                    print(f"  • {img['reference']} {img['caption'][:50]}...")

            # Layer 3: Epistemic Transparency
            print("\n🔍 LAYER 3: EPISTEMIC TRANSPARENCY")
            print("-" * 80)
            l3 = result["layers"]["l3_epistemic"]

            if l3.get("textual_analysis"):
                print("\nTextual Analysis:")
                print(f"  {l3['textual_analysis'][:200]}...")

            if l3.get("visual_analysis"):
                print("\nVisual Analysis:")
                print(f"  {l3['visual_analysis'][:200]}...")

        # Stats
        print("\n📊 STATISTICS")
        print("-" * 80)
        print(f"  Processing Time: {result['processing_time']:.2f}s")
        print(f"  Text Chunks: {result['retrieval']['stats']['text_retrieved']}")
        print(f"  Images: {result['retrieval']['stats']['images_retrieved']}")
        print(f"  Verdict: {result['critique']['verdict']}")

        if result['retrieval']['images']:
            print("\n📸 RETRIEVED IMAGES:")
            for i, img in enumerate(result['retrieval']['images'][:3], 1):
                caption = img.get('caption', 'No caption')
                similarity = img.get('similarity', 0)
                print(f"  {i}. {caption[:50]}... (similarity: {similarity:.2f})")

    async def run_category(self, category_index: int) -> None:
        """Run all queries in a category"""
        if 0 <= category_index < len(EXAMPLE_QUERIES):
            category = EXAMPLE_QUERIES[category_index]
            print(f"\n{'=' * 80}")
            print(f"CATEGORY: {category['category']}")
            print('=' * 80)

            for query in category["queries"]:
                await self.run_query(query)
                await asyncio.sleep(1)  # Brief pause between queries

    async def interactive_mode(self) -> None:
        """Run interactive demo mode"""
        print("\n" + "=" * 80)
        print("🏛️  HERITAGE LENS MULTIMODAL - INTERACTIVE DEMO")
        print("=" * 80)
        print("\nThis demo showcases the 3-layer multimodal output system:")
        print("  Layer 1: Answer with integrated visual context")
        print("  Layer 2: Source attribution (text and images)")
        print("  Layer 3: Epistemic transparency (bias analysis)")

        while True:
            print("\n" + "-" * 80)
            print("SELECT A CATEGORY:")
            for i, cat in enumerate(EXAMPLE_QUERIES, 1):
                print(f"  {i}. {cat['category']}")
            print("  5. Run all categories")
            print("  6. Custom query")
            print("  0. Exit")

            choice = input("\nEnter your choice (0-6): ").strip()

            if choice == "0":
                print("\nGoodbye! 👋")
                break
            elif choice in ["1", "2", "3", "4"]:
                await self.run_category(int(choice) - 1)
            elif choice == "5":
                for i in range(len(EXAMPLE_QUERIES)):
                    await self.run_category(i)
            elif choice == "6":
                query = input("\nEnter your query: ").strip()
                if query:
                    await self.run_query(query)
            else:
                print("Invalid choice. Please try again.")


async def quick_demo():
    """Run a quick demo with sample queries"""
    demo = HeritageLensDemo()

    print("\n" + "=" * 80)
    print("🏛️  HERITAGE LENS MULTIMODAL - QUICK DEMO")
    print("=" * 80)

    # Run a few example queries
    sample_queries = [
        "What are Olmec colossal heads?",
        "Describe Maya hieroglyphic writing",
    ]

    for query in sample_queries:
        await demo.run_query(query, show_details=True)
        print("\n" + "=" * 80)
        await asyncio.sleep(2)


def print_example_queries():
    """Print all example queries"""
    print("\n" + "=" * 80)
    print("📚 EXAMPLE QUERIES")
    print("=" * 80)

    for category in EXAMPLE_QUERIES:
        print(f"\n{category['category']}:")
        for query in category['queries']:
            print(f"  • {query}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Heritage Lens Multimodal Demo")
    parser.add_argument(
        "--mode",
        choices=["interactive", "quick", "examples"],
        default="interactive",
        help="Demo mode: interactive (default), quick, or examples"
    )

    args = parser.parse_args()

    if args.mode == "interactive":
        demo = HeritageLensDemo()
        asyncio.run(demo.interactive_mode())
    elif args.mode == "quick":
        asyncio.run(quick_demo())
    elif args.mode == "examples":
        print_example_queries()

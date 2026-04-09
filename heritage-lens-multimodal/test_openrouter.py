"""
Test OpenRouter API integration
"""

import sys
from pathlib import Path

sys.path.append(str(Path.home() / "heritage-lens-multimodal"))

from agents.synthesis.multimodal_synthesis_agent import MultimodalSynthesisAgent


def test_openrouter_connection():
    """Test direct OpenRouter API call"""
    print("=" * 60)
    print("Testing OpenRouter Integration")
    print("=" * 60)

    agent = MultimodalSynthesisAgent()
    api_key, base_url = agent._get_api_config()

    print(f"\nAPI Key: {api_key[:20]}...")
    print(f"Base URL: {base_url}")

    # Test using new OpenAI client format
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        print("\nSending test request to OpenRouter...")
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'OpenRouter integration working' and nothing else."}
            ],
            temperature=0.7,
            max_tokens=50
        )

        result = response.choices[0].message.content
        print(f"\nResponse: {result}")
        print("\n" + "=" * 60)
        print("✓ OpenRouter integration successful!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_openrouter_connection()
    sys.exit(0 if success else 1)

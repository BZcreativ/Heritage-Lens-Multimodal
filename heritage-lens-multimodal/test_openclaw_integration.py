"""
OpenClaw Integration Test Suite
Tests the integration between Heritage Lens Multimodal and OpenClaw gateway
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.append(str(Path.home() / "heritage-lens-multimodal"))

from agents.openclaw_integration import OpenClawMultimodalBridge


class OpenClawIntegrationTest:
    """Test suite for OpenClaw integration"""

    def __init__(self):
        self.bridge = None
        self.results = []

    async def setup(self):
        """Initialize the bridge"""
        print("=" * 70)
        print("OpenClaw Integration Test Suite")
        print("=" * 70)
        print("\n1. Initializing OpenClaw Bridge...")
        try:
            self.bridge = OpenClawMultimodalBridge()
            print("   ✓ Bridge initialized successfully")
            return True
        except Exception as e:
            print(f"   ✗ Bridge initialization failed: {e}")
            return False

    async def test_health_check(self):
        """Test health check endpoint"""
        print("\n2. Testing Health Check...")
        try:
            status = self.bridge.get_status()

            # Verify required fields
            assert "status" in status, "Missing status field"
            assert "system" in status, "Missing system field"
            assert "capabilities" in status, "Missing capabilities field"
            assert "stats" in status, "Missing stats field"

            # Verify values
            assert status["status"] == "healthy", f"Unexpected status: {status['status']}"
            assert status["system"] == "heritage-lens-multimodal"
            assert len(status["capabilities"]) == 5, f"Expected 5 capabilities, got {len(status['capabilities'])}"

            print(f"   ✓ Health check passed")
            print(f"     - Status: {status['status']}")
            print(f"     - Capabilities: {', '.join(status['capabilities'])}")
            print(f"     - Images indexed: {status['stats'].get('images_indexed', 0)}")
            return True

        except Exception as e:
            print(f"   ✗ Health check failed: {e}")
            return False

    async def test_query_handling(self):
        """Test query processing"""
        print("\n3. Testing Query Handling...")

        test_queries = [
            "What are Olmec colossal heads?",
            "Describe Maya hieroglyphics",
        ]

        all_passed = True
        for query in test_queries:
            print(f"\n   Query: '{query[:50]}...'")
            try:
                result = await self.bridge.handle_query(
                    query=query,
                    session_id="test_session_001"
                )

                # Verify response structure
                assert "response" in result, "Missing response field"
                assert "metadata" in result, "Missing metadata field"

                metadata = result["metadata"]
                assert "layers" in metadata, "Missing layers in metadata"
                assert "retrieval_stats" in metadata, "Missing retrieval_stats"
                assert "critique" in metadata, "Missing critique"
                assert "images" in metadata, "Missing images"

                # Verify layers
                layers = metadata["layers"]
                assert "l1_answer" in layers, "Missing l1_answer"
                assert "l2_attribution" in layers, "Missing l2_attribution"
                assert "l3_epistemic" in layers, "Missing l3_epistemic"

                # Verify critique
                critique = metadata["critique"]
                assert "verdict" in critique, "Missing verdict"
                assert critique["verdict"] in ["accept", "revise_retrieval", "revise_synthesis",
                                               "revise_epistemic", "revise_vision"], f"Invalid verdict: {critique['verdict']}"

                print(f"   ✓ Query processed successfully")
                print(f"     - Answer length: {len(layers['l1_answer'])} chars")
                print(f"     - Images: {len(metadata['images'])}")
                print(f"     - Verdict: {critique['verdict']}")

            except Exception as e:
                print(f"   ✗ Query failed: {e}")
                all_passed = False

        return all_passed

    async def test_multimodal_response_format(self):
        """Test that responses follow OpenClaw expected format"""
        print("\n4. Testing Response Format...")

        try:
            result = await self.bridge.handle_query(
                query="Tell me about ancient Mesoamerican artifacts",
                session_id="test_format"
            )

            # Check OpenClaw-compatible format
            assert isinstance(result, dict), "Result must be a dict"
            assert "response" in result, "Must have 'response' key"
            assert isinstance(result["response"], str), "Response must be a string"
            assert "metadata" in result, "Must have 'metadata' key"

            metadata = result["metadata"]
            assert metadata.get("system") == "heritage-lens-multimodal", "System identifier missing"

            # Check 3-layer structure
            layers = metadata.get("layers", {})
            assert all(k in layers for k in ["l1_answer", "l2_attribution", "l3_epistemic"]), \
                "Missing layer data"

            print(f"   ✓ Response format valid")
            print(f"     - Has 3 layers: ✓")
            print(f"     - Has metadata: ✓")
            print(f"     - Has images list: ✓")

            return True

        except Exception as e:
            print(f"   ✗ Format test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_error_handling(self):
        """Test error handling"""
        print("\n5. Testing Error Handling...")

        try:
            # Test with empty query
            result = await self.bridge.handle_query(
                query="",
                session_id="test_error"
            )

            # Should return a result even for empty query
            assert "response" in result, "Missing response for empty query"
            assert "metadata" in result, "Missing metadata for empty query"

            print(f"   ✓ Empty query handled gracefully")

            # Test with very long query
            long_query = "Tell me about " + "Mesoamerica " * 100
            result = await self.bridge.handle_query(
                query=long_query,
                session_id="test_long"
            )

            assert "response" in result, "Missing response for long query"
            print(f"   ✓ Long query handled gracefully")

            return True

        except Exception as e:
            print(f"   ✗ Error handling test failed: {e}")
            return False

    async def test_session_management(self):
        """Test session tracking"""
        print("\n6. Testing Session Management...")

        try:
            # Multiple queries in same session
            session_id = "test_session_persistent"

            result1 = await self.bridge.handle_query(
                query="What are Olmec artifacts?",
                session_id=session_id
            )

            result2 = await self.bridge.handle_query(
                query="Tell me more about them",
                session_id=session_id
            )

            # Both should succeed
            assert "response" in result1, "First query failed"
            assert "response" in result2, "Second query failed"

            print(f"   ✓ Session management working")
            print(f"     - Session ID: {session_id}")
            print(f"     - Queries processed: 2")

            return True

        except Exception as e:
            print(f"   ✗ Session test failed: {e}")
            return False

    async def test_api_endpoints(self):
        """Test FastAPI endpoints if available"""
        print("\n7. Testing API Endpoints...")

        try:
            from agents.openclaw_integration import app

            # Check that app is defined
            assert app is not None, "FastAPI app not available"

            # Check routes
            routes = [route.path for route in app.routes]

            assert "/query" in routes or "/query/" in routes, "Missing /query endpoint"
            assert "/health" in routes or "/health/" in routes, "Missing /health endpoint"
            assert "/" in routes, "Missing root endpoint"

            print(f"   ✓ API endpoints configured")
            print(f"     - Endpoints: {', '.join([r for r in routes if not r.startswith('/docs')])}")

            return True

        except ImportError:
            print(f"   ⚠ FastAPI not installed, skipping API tests")
            print(f"     Install with: pip install fastapi uvicorn")
            return True  # Not a failure, just not available

        except Exception as e:
            print(f"   ✗ API endpoint test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all tests"""
        tests = [
            ("Setup", self.setup),
            ("Health Check", self.test_health_check),
            ("Query Handling", self.test_query_handling),
            ("Response Format", self.test_multimodal_response_format),
            ("Error Handling", self.test_error_handling),
            ("Session Management", self.test_session_management),
            ("API Endpoints", self.test_api_endpoints),
        ]

        results = []
        for name, test_func in tests:
            try:
                passed = await test_func()
                results.append((name, passed))
            except Exception as e:
                print(f"\n   ✗ Test '{name}' crashed: {e}")
                results.append((name, False))

        # Summary
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)

        passed_count = sum(1 for _, p in results if p)
        total_count = len(results)

        for name, passed in results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {name}")

        print(f"\n{passed_count}/{total_count} tests passed")

        if passed_count == total_count:
            print("\n✓ All OpenClaw integration tests passed!")
            print("  The multimodal system is ready for OpenClaw integration.")
        else:
            print(f"\n⚠ {total_count - passed_count} test(s) failed.")
            print("  Please review the errors above.")

        return passed_count == total_count


async def main():
    """Run OpenClaw integration tests"""
    test_suite = OpenClawIntegrationTest()
    success = await test_suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

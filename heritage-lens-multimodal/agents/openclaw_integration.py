"""
OpenClaw Integration Module
Connects Heritage Lens multimodal system with OpenClaw gateway
"""

import asyncio
import json
from typing import Dict, Any, Optional
from pathlib import Path

# Detect project root - works in both Docker and local environments
PROJECT_ROOT = Path("/app") if Path("/app").exists() else (Path.home() / "heritage-lens-multimodal")



class OpenClawMultimodalBridge:
    """
    Bridge between Heritage Lens multimodal system and OpenClaw gateway
    Enables OpenClaw to route queries through the multimodal orchestrator
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self.orchestrator = None
        self._init_orchestrator()

    def _init_orchestrator(self):
        """Initialize the multimodal orchestrator"""
        import sys
        sys.path.append(str(PROJECT_ROOT))
        from agents.orchestrator import EnhancedOrchestrator
        self.orchestrator = EnhancedOrchestrator(self.config_path)

    async def handle_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Handle a query from OpenClaw

        Args:
            query: User query string
            session_id: Optional session identifier
            context: Optional context from OpenClaw

        Returns:
            Formatted response for OpenClaw
        """
        # Set defaults from context or use standard values
        top_k_text = context.get("top_k_text", 5) if context else 5
        top_k_images = context.get("top_k_images", 3) if context else 3
        strict_corpus = context.get("strict_corpus", True) if context else True
        document_scope = context.get("document_scope") if context else None

        # Process through orchestrator
        result = await self.orchestrator.process_query(
            query=query,
            session_id=session_id or "openclaw_default",
            top_k_text=top_k_text,
            top_k_images=top_k_images,
            strict_corpus=strict_corpus,
            document_scope=document_scope
        )

        # Return raw result for UI compatibility
        # (OpenClaw formatting handled separately for gateway responses)
        return result

    def _format_openclaw_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format orchestrator output for OpenClaw"""
        layers = result["layers"]
        retrieval = result["retrieval"]
        critique = result["critique"]

        # Build formatted answer with layers
        formatted_response = self._build_formatted_answer(layers, retrieval)

        return {
            "response": formatted_response,
            "metadata": {
                "system": "heritage-lens-multimodal",
                "layers": {
                    "l1_answer": layers["l1_answer"],
                    "l2_attribution": layers["l2_attribution"],
                    "l3_epistemic": layers["l3_epistemic"]
                },
                "retrieval_stats": retrieval["stats"],
                "critique": {
                    "verdict": critique["verdict"],
                    "confidence": critique.get("confidence"),
                    "multimodal_coherence": critique.get("multimodal_coherence")
                },
                "images": [
                    {
                        "path": img["path"],
                        "caption": img.get("caption", ""),
                        "similarity": img["similarity"]
                    }
                    for img in retrieval["images"]
                ],
                "processing_time": result["processing_time"],
                "revisions": result["revisions"]
            }
        }

    def _build_formatted_answer(
        self,
        layers: Dict[str, Any],
        retrieval: Dict[str, Any]
    ) -> str:
        """Build human-readable formatted answer"""
        answer = layers["l1_answer"]

        # Add image references if images were retrieved
        if retrieval["images"]:
            answer += "\n\n**📸 Related Images:**\n"
            for i, img in enumerate(retrieval["images"][:3], 1):
                caption = img.get("caption", f"Image {i}")
                answer += f"\n- {caption}"

        return answer

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator stats for UI compatibility"""
        return self.orchestrator.get_stats()

    def get_status(self) -> Dict[str, Any]:
        """Get system status for OpenClaw health checks"""
        stats = self.orchestrator.get_stats()

        return {
            "status": "healthy",
            "system": "heritage-lens-multimodal",
            "version": "1.0.0",
            "capabilities": [
                "text_retrieval",
                "image_retrieval",
                "multimodal_synthesis",
                "epistemic_analysis",
                "3_layer_output"
            ],
            "stats": stats
        }


# FastAPI endpoint handler for OpenClaw integration
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel

    app = FastAPI(title="Heritage Lens OpenClaw Bridge")

    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None
        context: Optional[Dict[str, Any]] = None

    class QueryResponse(BaseModel):
        response: str
        metadata: Dict[str, Any]

    # Global bridge instance
    _bridge = None

    def get_bridge():
        global _bridge
        if _bridge is None:
            _bridge = OpenClawMultimodalBridge()
        return _bridge

    @app.post("/query", response_model=QueryResponse)
    async def query_endpoint(request: QueryRequest):
        """Main query endpoint for OpenClaw integration"""
        try:
            bridge = get_bridge()
            result = await bridge.handle_query(
                query=request.query,
                session_id=request.session_id,
                context=request.context
            )
            return QueryResponse(**result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health")
    async def health_endpoint():
        """Health check endpoint"""
        try:
            bridge = get_bridge()
            return bridge.get_status()
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/")
    async def root():
        """Root endpoint with basic info"""
        return {
            "name": "Heritage Lens OpenClaw Bridge",
            "version": "1.0.0",
            "endpoints": ["/query", "/health"]
        }

except ImportError:
    # FastAPI not installed, skip API endpoints
    pass


# CLI interface for testing
async def main():
    """CLI for testing OpenClaw integration"""
    import argparse

    parser = argparse.ArgumentParser(description="Heritage Lens OpenClaw Bridge")
    parser.add_argument("query", help="Query to process")
    parser.add_argument("--session-id", help="Session identifier")
    parser.add_argument("--top-k-text", type=int, default=5, help="Number of text chunks")
    parser.add_argument("--top-k-images", type=int, default=3, help="Number of images")

    args = parser.parse_args()

    bridge = OpenClawMultimodalBridge()

    context = {
        "top_k_text": args.top_k_text,
        "top_k_images": args.top_k_images
    }

    result = await bridge.handle_query(
        query=args.query,
        session_id=args.session_id,
        context=context
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

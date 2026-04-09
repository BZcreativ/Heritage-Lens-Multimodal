"""
Heritage Lens API Server
FastAPI wrapper exposing Qdrant, LlamaIndex, and agent capabilities for OpenClaw
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from contextlib import asynccontextmanager

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Heritage Lens imports
import sys
sys.path.append(str(Path.home() / "heritage-lens-multimodal"))

from agents.orchestrator import EnhancedOrchestrator
from agents.openclaw_integration import OpenClawMultimodalBridge
from agents.vision.vision_agent import VisionAgent
from tools.slack_file_handler import SlackFileHandler


# Global instances
_bridge: Optional[OpenClawMultimodalBridge] = None
_orchestrator: Optional[EnhancedOrchestrator] = None
_vision_agent: Optional[VisionAgent] = None


def get_bridge() -> OpenClawMultimodalBridge:
    """Get or create bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = OpenClawMultimodalBridge()
    return _bridge


def get_orchestrator() -> EnhancedOrchestrator:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EnhancedOrchestrator()
    return _orchestrator


def get_vision_agent() -> VisionAgent:
    """Get or create vision agent instance"""
    global _vision_agent
    if _vision_agent is None:
        _vision_agent = VisionAgent()
    return _vision_agent


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    top_k_text: int = 5
    top_k_images: int = 3


class QueryResponse(BaseModel):
    response: str
    metadata: Dict[str, Any]


class SlackFileRequest(BaseModel):
    file_id: str
    index: bool = True


class IndexDocumentsRequest(BaseModel):
    pdf_dir: str
    extract_images: bool = True


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class StatusResponse(BaseModel):
    status: str
    system: str
    capabilities: List[str]
    qdrant_connected: bool
    llama_index_ready: bool
    vision_enabled: bool


# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting Heritage Lens API Server...")
    try:
        get_bridge()
        print("✅ Bridge initialized")
    except Exception as e:
        print(f"⚠️ Bridge initialization failed: {e}")

    try:
        get_vision_agent()
        print("✅ Vision agent initialized")
    except Exception as e:
        print(f"⚠️ Vision agent initialization failed: {e}")

    yield

    # Shutdown
    print("🛑 Shutting down Heritage Lens API Server...")


# Create FastAPI app
app = FastAPI(
    title="Heritage Lens Multimodal API",
    description="API for Qdrant, LlamaIndex, and multimodal agent operations",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health", response_model=StatusResponse)
async def health_check():
    """Get system health status"""
    try:
        bridge = get_bridge()
        status = bridge.get_status()

        # Check Qdrant
        qdrant_connected = False
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(url="http://localhost:6333")
            client.get_collections()
            qdrant_connected = True
        except:
            pass

        # Check vision
        vision_enabled = False
        try:
            vision = get_vision_agent()
            vision_enabled = vision is not None
        except:
            pass

        return StatusResponse(
            status=status["status"],
            system=status["system"],
            capabilities=status["capabilities"],
            qdrant_connected=qdrant_connected,
            llama_index_ready=True,  # Bridge initialized means LLM ready
            vision_enabled=vision_enabled
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# Query endpoint
@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Process a heritage query"""
    try:
        bridge = get_bridge()

        context = {
            "top_k_text": request.top_k_text,
            "top_k_images": request.top_k_images
        }

        result = await bridge.handle_query(
            query=request.query,
            session_id=request.session_id,
            context=context
        )

        return QueryResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


# Slack file download endpoint
@app.post("/slack/download")
async def slack_download(request: SlackFileRequest):
    """Download and optionally index a Slack file"""
    try:
        handler = SlackFileHandler()

        if request.index:
            result = handler.index_slack_file(request.file_id)
        else:
            result = handler.download_file(request.file_id)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Slack file handling failed: {str(e)}")


# Document indexing endpoint
@app.post("/index/documents")
async def index_documents(
    request: IndexDocumentsRequest,
    background_tasks: BackgroundTasks
):
    """Index documents from a directory"""
    try:
        pdf_path = Path(request.pdf_dir)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {request.pdf_dir}")

        # Run indexing in background
        async def do_index():
            from pipelines.pdf_extraction.multimodal_ingest import MultimodalIngestPipeline
            ingest = MultimodalIngestPipeline(
                extract_images=request.extract_images
            )
            await ingest.ingest_pdf_directory(pdf_path)

        background_tasks.add_task(do_index)

        return {
            "status": "indexing_started",
            "pdf_dir": str(pdf_path),
            "extract_images": request.extract_images
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


# Image indexing endpoint
@app.post("/index/images")
async def index_images(
    request: IndexDocumentsRequest,
    background_tasks: BackgroundTasks
):
    """Index images from PDFs"""
    try:
        pdf_path = Path(request.pdf_dir)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {request.pdf_dir}")

        # Run indexing in background
        async def do_index():
            import subprocess
            subprocess.run([
                "python", "scripts/index_images.py",
                "--pdf-dir", str(pdf_path)
            ])

        background_tasks.add_task(do_index)

        return {
            "status": "image_indexing_started",
            "pdf_dir": str(pdf_path)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image indexing failed: {str(e)}")


# Search endpoint (direct Qdrant/LlamaIndex access)
@app.post("/search/text")
async def search_text(request: SearchRequest):
    """Search text documents directly"""
    try:
        from llama_index.core import VectorStoreIndex
        from llama_index.vector_stores.qdrant import QdrantVectorStore
        from llama_index.embeddings.openai import OpenAIEmbedding
        from qdrant_client import QdrantClient

        # Initialize clients
        client = QdrantClient(url="http://localhost:6333")
        vector_store = QdrantVectorStore(
            client=client,
            collection_name="heritage_lens_text"
        )

        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=OpenAIEmbedding()
        )

        # Search
        retriever = index.as_retriever(similarity_top_k=request.top_k)
        nodes = retriever.retrieve(request.query)

        results = []
        for node in nodes:
            results.append({
                "text": node.node.text,
                "metadata": node.node.metadata,
                "score": node.score if hasattr(node, 'score') else None
            })

        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Image search endpoint
@app.post("/search/images")
async def search_images(request: SearchRequest):
    """Search images using CLIP"""
    try:
        vision = get_vision_agent()
        results = await vision.search_images(request.query, request.top_k)

        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")


# Qdrant direct access endpoints
@app.get("/qdrant/collections")
async def qdrant_collections():
    """List Qdrant collections"""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url="http://localhost:6333")
        collections = client.get_collections()

        return {
            "collections": [
                {"name": c.name} for c in collections.collections
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Qdrant unavailable: {str(e)}")


@app.get("/qdrant/collections/{collection_name}/info")
async def qdrant_collection_info(collection_name: str):
    """Get Qdrant collection info"""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url="http://localhost:6333")
        info = client.get_collection(collection_name)

        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "status": info.status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection info: {str(e)}")


# Root endpoint
@app.get("/")
async def root():
    """API root with available endpoints"""
    return {
        "name": "Heritage Lens Multimodal API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "/query",
            "slack_download": "/slack/download",
            "index_documents": "/index/documents",
            "index_images": "/index/images",
            "search_text": "/search/text",
            "search_images": "/search/images",
            "qdrant_collections": "/qdrant/collections"
        }
    }


# CLI entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Multimodal Retrieval Sub-Agent
Unified text and image retrieval with page-aware matching
"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml

# Detect project root - works in both Docker and local environments
if Path("/app").exists():
    PROJECT_ROOT = Path("/app")
elif (Path("/home/heritage") / "heritage-lens-multimodal").exists():
    PROJECT_ROOT = Path("/home/heritage") / "heritage-lens-multimodal"
else:
    PROJECT_ROOT = Path.home() / "heritage-lens-multimodal"



class MultimodalRetrievalAgent:
    def __init__(self, config_path: str = "config/settings.yaml"):
        config_full_path = Path(config_path)
        if not config_full_path.is_absolute():
            config_full_path = PROJECT_ROOT / config_path

        with open(config_full_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Import vision agent
        import sys
        sys.path.append(str(PROJECT_ROOT))
        from agents.vision.vision_agent import VisionAgent

        self.vision_agent = VisionAgent(config_path)

        # Text retrieval will be initialized on first use
        self._text_index = None
        self.text_parser = None
        self._qdrant_client = None

    def _load_env_file(self):
        """Load environment variables from .env file"""
        import os
        from pathlib import Path

        env_path = PROJECT_ROOT / "config" / ".env"
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        # Only set if not already set in environment
                        if key not in os.environ:
                            os.environ[key] = value

    def _get_qdrant_client(self):
        """Lazy load Qdrant client"""
        if self._qdrant_client is None:
            try:
                from qdrant_client import QdrantClient
                import os

                # Get Qdrant URL from config
                qdrant_url = self.config["vector_db"]["text"]["qdrant"]["url"]

                # Override with environment variable if set (for Docker)
                qdrant_url = os.getenv("QDRANT_URL", qdrant_url)

                # Convert localhost to qdrant for Docker networking
                if "localhost" in qdrant_url:
                    qdrant_url = qdrant_url.replace("localhost", "qdrant")

                self._qdrant_client = QdrantClient(url=qdrant_url)
            except Exception as e:
                print(f"Warning: Could not connect to Qdrant: {e}")
                self._qdrant_client = None
        return self._qdrant_client

    def _init_text_retrieval(self):
        """Initialize text retrieval with LlamaIndex if available"""
        if self._text_index is not None:
            return

        # Load environment variables from .env file
        self._load_env_file()

        try:
            from llama_index.core import VectorStoreIndex, StorageContext, Settings
            from llama_index.vector_stores.qdrant import QdrantVectorStore

            qdrant_client = self._get_qdrant_client()
            if qdrant_client is None:
                return

            # Try to initialize embedding model - prefer local embeddings
            embed_model = self._get_embedding_model()
            if embed_model is None:
                print("Warning: No embedding model available. Text retrieval disabled.")
                self._text_index = None
                return

            # Set global settings
            Settings.embed_model = embed_model

            # Create vector store
            vector_store = QdrantVectorStore(
                client=qdrant_client,
                collection_name=self.config["vector_db"]["text"]["qdrant"]["collection"]
            )

            # Create storage context
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            # Create empty index (will be populated during ingestion)
            self._text_index = VectorStoreIndex(
                [],
                storage_context=storage_context,
                embed_model=embed_model
            )

            print("✓ Text retrieval initialized with LlamaIndex + Qdrant")

        except ImportError:
            print("Warning: LlamaIndex not installed. Text retrieval will be limited.")
            self._text_index = None
        except Exception as e:
            print(f"Warning: Could not initialize text retrieval: {e}")
            self._text_index = None

    def _get_embedding_model(self):
        """Get embedding model - prefer local, fallback to OpenAI"""
        import os

        # Check if OpenAI key is valid (not placeholder)
        openai_key = os.getenv("OPENAI_API_KEY", "")
        has_valid_openai = openai_key and not openai_key.startswith("sk-xxxxx") and len(openai_key) > 20

        if has_valid_openai:
            try:
                from llama_index.embeddings.openai import OpenAIEmbedding
                print("  Using OpenAI embeddings")
                return OpenAIEmbedding()
            except Exception as e:
                print(f"  OpenAI embedding failed: {e}")

        # Fallback to local sentence-transformers
        try:
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding

            # Use a lightweight multilingual model
            model_name = self.config.get("embeddings", {}).get("model", "sentence-transformers/all-MiniLM-L6-v2")
            print(f"  Using local embeddings: {model_name}")
            return HuggingFaceEmbedding(model_name=model_name)
        except ImportError:
            print("  Warning: HuggingFaceEmbedding not available. Install with: pip install llama-index-embeddings-huggingface")
        except Exception as e:
            print(f"  Local embedding failed: {e}")

        return None

    async def retrieve(
        self,
        query: str,
        top_k_text: int = None,
        top_k_images: int = None,
        document_scope: List[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant text chunks and images for the query

        Args:
            query: User query
            top_k_text: Number of text chunks to retrieve
            top_k_images: Number of images to retrieve
            document_scope: Optional list of document IDs/filenames to scope retrieval to

        Returns:
            Dict with text chunks, images, and unified results
        """
        top_k_text = top_k_text or self.config["retrieval"]["text"]["top_k"]
        top_k_images = top_k_images or self.config["retrieval"]["image"]["top_k"]

        # Retrieve text chunks using LlamaIndex if available
        text_results = await self._retrieve_text(query, top_k_text, document_scope)

        # Retrieve images with document scope if specified
        image_results = await self.vision_agent.search_images(query, top_k_images, document_scope)

        # Perform page-aware matching if enabled
        if self.config["retrieval"]["image"]["page_aware_matching"]:
            matched_images = self._page_aware_matching(text_results, image_results)
        else:
            matched_images = image_results

        return {
            "text_chunks": text_results,
            "images": matched_images,
            "query": query,
            "document_scope": document_scope,
            "stats": {
                "text_retrieved": len(text_results),
                "images_retrieved": len(matched_images),
                "multimodal": len(text_results) > 0 and len(matched_images) > 0,
                "scoped": document_scope is not None
            }
        }

    async def _retrieve_text(
        self,
        query: str,
        top_k: int,
        document_scope: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve text chunks using LlamaIndex with Qdrant, optionally scoped to specific documents"""
        self._init_text_retrieval()

        if self._text_index is None:
            # Fallback: return empty list if text retrieval not available
            return []

        try:
            # Create query engine with optional document filter
            from llama_index.core.retrievers import VectorIndexRetriever
            from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

            # Build metadata filters for document scoping
            filters = None
            if document_scope:
                # Create filters for document scope - match by source filename or doc_id
                filter_list = []
                for doc_id in document_scope:
                    filter_list.append(ExactMatchFilter(key="source", value=doc_id))
                    # Also match by doc_id if stored differently
                    filter_list.append(ExactMatchFilter(key="doc_id", value=doc_id))

                if filter_list:
                    filters = MetadataFilters(filters=filter_list, condition="or")
                    print(f"  Applying document scope filter: {document_scope}")

            retriever = VectorIndexRetriever(
                index=self._text_index,
                similarity_top_k=top_k,
                filters=filters
            )

            # Retrieve nodes
            nodes = retriever.retrieve(query)

            # Format results
            results = []
            for node in nodes:
                results.append({
                    "content": node.node.text,
                    "metadata": node.node.metadata,
                    "similarity": node.score if hasattr(node, 'score') else 0.0
                })

            return results

        except Exception as e:
            print(f"Error in text retrieval: {e}")
            return []

    def _page_aware_matching(self, text_chunks: List[Dict], image_results: List[Dict]) -> List[Dict]:
        """
        Match images to text chunks based on page numbers
        """
        if not text_chunks or not image_results:
            return image_results

        # Get average page from text chunks
        text_pages = []
        for chunk in text_chunks:
            page = chunk.get("metadata", {}).get("page")
            if page is not None:
                text_pages.append(page)

        if not text_pages:
            return image_results

        avg_page = sum(text_pages) / len(text_pages)
        page_tolerance = self.config["retrieval"]["image"]["page_tolerance"]

        # Score images based on page proximity
        scored_images = []
        for img in image_results:
            img_page = img.get("metadata", {}).get("page")
            if img_page is not None:
                page_distance = abs(img_page - avg_page)
                if page_distance <= page_tolerance:
                    # Adjust similarity score based on page proximity
                    proximity_factor = 1.0 - (page_distance / page_tolerance)
                    adjusted_score = img["similarity"] * (0.7 + 0.3 * proximity_factor)
                    img["adjusted_score"] = adjusted_score
                    scored_images.append(img)

        # Sort by adjusted score
        scored_images.sort(key=lambda x: x.get("adjusted_score", x["similarity"]), reverse=True)

        return scored_images

    def index_documents(self, documents: List[Any]):
        """
        Index documents for text retrieval

        Args:
            documents: List of LlamaIndex Document objects
        """
        self._init_text_retrieval()

        if self._text_index is None:
            raise RuntimeError("Text retrieval not initialized. Check Qdrant connection.")

        try:
            from llama_index.core.node_parser import SentenceSplitter

            # Parse documents into nodes
            parser = SentenceSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            nodes = parser.get_nodes_from_documents(documents)

            # Add nodes to index
            self._text_index.insert_nodes(nodes)

            print(f"✓ Indexed {len(documents)} documents ({len(nodes)} chunks)")

        except Exception as e:
            print(f"Error indexing documents: {e}")
            raise

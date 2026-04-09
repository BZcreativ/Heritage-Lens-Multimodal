"""
Optional Vision Service - Can be disabled without affecting core functionality
Implements graceful degradation when vision dependencies are not available
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class OptionalVisionService:
    """
    Optional vision service with dependency checking and graceful degradation.
    Can be disabled via configuration or when dependencies are missing.
    """

    def __init__(self, enabled: bool = True, config_path: str = "config/settings.yaml"):
        """
        Initialize vision service with optional feature flag

        Args:
            enabled: Whether vision features are enabled
            config_path: Path to configuration file
        """
        self.enabled = enabled
        self.model = None
        self.image_store = None
        self.config = {}

        # Load config to check feature flags
        try:
            import yaml
            config_full_path = Path(config_path)
            if not config_full_path.is_absolute():
                config_full_path = Path.home() / "heritage-lens-multimodal" / config_path

            with open(config_full_path, "r") as f:
                full_config = yaml.safe_load(f)
                self.config = full_config.get("multimodal", {}).get("vision", {})

            # Check if multimodal is enabled in config
            if not full_config.get("multimodal", {}).get("enabled", True):
                self.enabled = False
                logger.info("Vision service disabled via configuration (multimodal.enabled: false)")
                return

            if not full_config.get("multimodal", {}).get("vision", {}).get("enabled", True):
                self.enabled = False
                logger.info("Vision service disabled via configuration (multimodal.vision.enabled: false)")
                return

        except Exception as e:
            logger.warning(f"Could not load config for vision service: {e}")

        if not self.enabled:
            logger.info("Vision service disabled")
            return

        # Try to initialize vision components
        self._initialize_vision()

    def _initialize_vision(self):
        """Initialize vision components with graceful error handling"""
        try:
            # Optional imports - these may not be installed
            from sentence_transformers import SentenceTransformer
            from qdrant_client import QdrantClient

            # Initialize CLIP model
            model_name = self.config.get("model", "clip-ViT-B-32")
            logger.info(f"Loading CLIP model: {model_name}")
            self.model = SentenceTransformer(model_name)

            # Initialize image store connection
            qdrant_url = self.config.get("qdrant_url", "http://localhost:6333")
            self.image_store = QdrantClient(url=qdrant_url)

            # Test connection
            self.image_store.get_collections()

            logger.info("✅ Optional vision service initialized successfully")

        except ImportError as e:
            logger.warning(f"Vision dependencies not installed: {e}")
            logger.warning("Vision service will be unavailable. To enable, install: pip install sentence-transformers qdrant-client")
            self.enabled = False
            self.model = None
            self.image_store = None

        except Exception as e:
            logger.error(f"Vision service initialization failed: {e}")
            logger.warning("Vision service will be unavailable")
            self.enabled = False
            self.model = None
            self.image_store = None

    async def search_images(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar images - returns empty list if disabled

        Args:
            query: Text query to search for
            top_k: Number of results to return

        Returns:
            List of image results or empty list if disabled
        """
        if not self.enabled or not self.model or not self.image_store:
            return []

        try:
            # Generate query embedding
            query_embedding = self.model.encode(query)

            # Get collection name
            collection_name = self.config.get("image_collection", "heritage_lens_images")

            # Search in image collection
            results = self.image_store.search(
                collection_name=collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k
            )

            return [
                {
                    "id": hit.id,
                    "similarity": hit.score,
                    "metadata": hit.payload,
                    "path": hit.payload.get("path", ""),
                    "caption": hit.payload.get("caption", ""),
                    "source": hit.payload.get("source", "Unknown")
                }
                for hit in results
            ]

        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return []  # Graceful degradation

    async def encode_image(self, image_path: str) -> Optional[List[float]]:
        """
        Encode an image to embedding vector

        Args:
            image_path: Path to image file

        Returns:
            Embedding vector or None if disabled/error
        """
        if not self.enabled or not self.model:
            return None

        try:
            from PIL import Image
            image = Image.open(image_path)
            embedding = self.model.encode(image)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            return None

    def is_available(self) -> bool:
        """Check if vision capabilities are available"""
        return self.enabled and self.model is not None and self.image_store is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get vision service statistics"""
        return {
            "enabled": self.enabled,
            "available": self.is_available(),
            "model": self.config.get("model", "clip-ViT-B-32") if self.enabled else None,
            "collection": self.config.get("image_collection", "heritage_lens_images") if self.enabled else None
        }


class VisionServiceStub:
    """
    Stub implementation for when vision is completely disabled.
    Provides the same interface but all methods return empty/default values.
    """

    def __init__(self):
        self.enabled = False
        self.model = None
        self.image_store = None

    async def search_images(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Always returns empty list"""
        return []

    async def encode_image(self, image_path: str) -> Optional[List[float]]:
        """Always returns None"""
        return None

    def is_available(self) -> bool:
        """Always returns False"""
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Returns disabled stats"""
        return {
            "enabled": False,
            "available": False,
            "model": None,
            "collection": None
        }


def create_vision_service(config_path: str = "config/settings.yaml") -> OptionalVisionService:
    """
    Factory function to create vision service with proper configuration

    Args:
        config_path: Path to configuration file

    Returns:
        Configured OptionalVisionService instance
    """
    try:
        import yaml
        config_full_path = Path(config_path)
        if not config_full_path.is_absolute():
            config_full_path = Path.home() / "heritage-lens-multimodal" / config_path

        with open(config_full_path, "r") as f:
            config = yaml.safe_load(f)

        # Check if multimodal is enabled
        multimodal_enabled = config.get("multimodal", {}).get("enabled", True)
        vision_enabled = config.get("multimodal", {}).get("vision", {}).get("enabled", True)

        if not multimodal_enabled or not vision_enabled:
            logger.info("Vision service disabled by configuration")
            return VisionServiceStub()

        return OptionalVisionService(enabled=True, config_path=config_path)

    except Exception as e:
        logger.warning(f"Failed to create vision service: {e}")
        return VisionServiceStub()

"""
Vision Sub-Agent
Handles image embedding (CLIP), similarity search, and cultural analysis (GLM-4V)
"""

import os
import pickle
import base64
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml
from PIL import Image

# Detect project root - works in both Docker and local environments
if Path("/app").exists():
    PROJECT_ROOT = Path("/app")
elif (Path("/home/heritage") / "heritage-lens-multimodal").exists():
    PROJECT_ROOT = Path("/home/heritage") / "heritage-lens-multimodal"
else:
    PROJECT_ROOT = Path.home() / "heritage-lens-multimodal"



class VisionAgent:
    """
    Vision agent combining CLIP embeddings for similarity search
    and GLM-4V for enhanced caption generation and cultural analysis
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        config_full_path = Path(config_path)
        if not config_full_path.is_absolute():
            config_full_path = PROJECT_ROOT / config_path

        with open(config_full_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Lazy load CLIP model
        self._clip_model = None
        self.cache_dir = Path(self.config["vision"]["cache_dir"])
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.similarity_threshold = self.config["vision"]["similarity_threshold"]

        # GLM-4V configuration
        self._glm_api_key = None
        self._glm_client = None
        self.glm_enabled = self._check_glm_config()

        # Load or create embedding cache
        self.image_paths, self.image_embeddings = self._load_embeddings_cache()
        self.image_metadata = self._load_metadata_cache()

    def _check_glm_config(self) -> bool:
        """Check if GLM-4V API is configured"""
        # Try environment first
        api_key = os.getenv("GLM_API_KEY")
        if api_key:
            self._glm_api_key = api_key
            return True

        # Try .env file
        env_path = PROJECT_ROOT / "config" / ".env"
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("GLM_API_KEY="):
                        val = line.split("=", 1)[1].strip()
                        if val and not val.startswith("xxx"):
                            self._glm_api_key = val
                            return True
        return False

    @property
    def clip_model(self):
        """Lazy load CLIP model"""
        if self._clip_model is None:
            from sentence_transformers import SentenceTransformer
            self._clip_model = SentenceTransformer(self.config["vision"]["model"])
        return self._clip_model

    def _get_glm_client(self):
        """Get GLM-4V client (OpenAI-compatible)"""
        if self._glm_client is None and self.glm_enabled:
            from openai import OpenAI
            # Z.ai uses OpenAI-compatible API
            self._glm_client = OpenAI(
                api_key=self._glm_api_key,
                base_url="https://api.z.ai/v1"
            )
        return self._glm_client

    async def search_images(
        self,
        query: str,
        top_k: int = 3,
        document_scope: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar images using CLIP embeddings
        Falls back to Qdrant search if local cache is empty

        Args:
            query: Search query
            top_k: Number of images to retrieve
            document_scope: Optional list of document IDs/filenames to scope search to
        """
        # First try local cache (fast path)
        local_results = await self._search_local_cache(query, top_k, document_scope)

        # If local cache has results, use them
        if local_results:
            return local_results

        # Fallback: Search Qdrant when local cache is empty
        print(f"  Local cache empty, searching Qdrant for: {query[:50]}...")
        qdrant_results = await self._search_qdrant_images(query, top_k, document_scope)

        if qdrant_results:
            print(f"  Found {len(qdrant_results)} images in Qdrant")

        return qdrant_results

    async def _search_local_cache(
        self,
        query: str,
        top_k: int = 3,
        document_scope: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Search local embeddings cache"""
        if len(self.image_embeddings) == 0:
            return []

        from sentence_transformers.util import cos_sim

        # Encode query
        query_embedding = self.clip_model.encode(query)

        # Calculate similarities
        similarities = cos_sim(query_embedding, self.image_embeddings)[0]

        # Get top-k indices (get more initially in case we filter some out)
        search_k = top_k * 3 if document_scope else top_k
        top_indices = np.array(similarities).argsort()[-search_k:][::-1]

        # Filter by threshold and document scope
        results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            if similarity < self.similarity_threshold:
                continue

            image_path = self.image_paths[idx]
            metadata = self.image_metadata.get(image_path, {})

            # Apply document scope filter if specified
            if document_scope:
                source_doc = metadata.get("source", "")
                extracted_from = metadata.get("extracted_from", "")

                # Check if image belongs to any of the scoped documents
                scope_match = False
                for scope_doc in document_scope:
                    if scope_doc in source_doc or scope_doc in extracted_from:
                        scope_match = True
                        break

                if not scope_match:
                    continue

            # Get enhanced caption using GLM-4V if available
            caption = await self.generate_caption(image_path)

            results.append({
                "path": image_path,
                "similarity": similarity,
                "metadata": metadata,
                "caption": caption
            })

            if len(results) >= top_k:
                break

        return results

    async def _search_qdrant_images(
        self,
        query: str,
        top_k: int = 3,
        document_scope: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Qdrant for similar images when local cache is empty
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Filter, FieldCondition, MatchAny
            import os

            # Get Qdrant configuration
            qdrant_config = self.config.get("qdrant", {})
            if not qdrant_config:
                vector_db_config = self.config.get("vector_db", {})
                text_config = vector_db_config.get("text", {})
                qdrant_config = text_config.get("qdrant", {})

            qdrant_url = qdrant_config.get("url", "http://localhost:6333")
            qdrant_url = os.getenv("QDRANT_URL", qdrant_url)
            if "localhost" in qdrant_url:
                qdrant_url = qdrant_url.replace("localhost", "qdrant")

            collection_name = self.config.get("multimodal", {}).get("vision", {}).get("image_collection", "heritage_lens_images")

            # Connect to Qdrant
            qdrant = QdrantClient(url=qdrant_url)

            # Encode query using CLIP
            query_embedding = self.clip_model.encode(query).tolist()

            # Build filter for document scope if specified
            search_filter = None
            if document_scope:
                # Create filter for source field matching any of the scope documents
                search_filter = Filter(
                    should=[
                        FieldCondition(key="source", match=MatchAny(any=document_scope))
                    ]
                )

            # Search Qdrant using query_points
            # Use lower threshold for Qdrant search (CLIP embeddings have lower scores)
            qdrant_threshold = min(self.similarity_threshold, 0.2)

            search_result = qdrant.query_points(
                collection_name=collection_name,
                query=query_embedding,
                limit=top_k,
                query_filter=search_filter,
                score_threshold=qdrant_threshold,
                with_payload=True,
                with_vectors=False
            )

            # Convert results to expected format
            results = []
            for point in search_result.points:
                image_path = point.payload.get("path", "")
                similarity = point.score

                # Build metadata from payload
                metadata = {
                    "source": point.payload.get("source", "unknown"),
                    "page": point.payload.get("page", 0),
                    **{k: v for k, v in point.payload.items() if k not in ["path", "source", "page"]}
                }

                # Try to get caption - check metadata first, then generate
                caption = point.payload.get("caption", "")
                if not caption and image_path:
                    try:
                        caption = await self.generate_caption(image_path)
                    except Exception as e:
                        caption = f"Image from {metadata.get('source', 'document')}"

                results.append({
                    "path": image_path,
                    "similarity": similarity,
                    "metadata": metadata,
                    "caption": caption or f"Image from {metadata.get('source', 'document')}"
                })

            return results

        except Exception as e:
            print(f"  Error searching Qdrant images: {e}")
            return []

    async def generate_caption(self, image_path: str) -> str:
        """
        Generate a descriptive caption for an image.
        Uses GLM-4V if available, otherwise falls back to CLIP-based captioning.
        """
        # Try GLM-4V first for enhanced captioning
        if self.glm_enabled:
            try:
                return await self._generate_glm_caption(image_path)
            except Exception as e:
                print(f"GLM-4V caption failed, using fallback: {e}")

        # Fallback to CLIP-based captioning
        return await self._generate_clip_caption(image_path)

    async def _generate_glm_caption(self, image_path: str) -> str:
        """Generate caption using GLM-4V via Z.ai API"""
        client = self._get_glm_client()
        if not client:
            raise RuntimeError("GLM-4V not configured")

        # Encode image to base64
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        # Determine image format
        ext = Path(image_path).suffix.lower()
        mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"

        # Call GLM-4V
        response = client.chat.completions.create(
            model="glm-4v",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this cultural heritage artifact or image. Focus on: 1) What is shown, 2) Key visual features, 3) Cultural context if identifiable. Be concise (2-3 sentences)."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    async def _generate_clip_caption(self, image_path: str) -> str:
        """Generate caption using CLIP similarity to cultural terms"""
        try:
            img = Image.open(image_path).convert("RGB")

            # Cultural heritage terms for CLIP matching
            cultural_terms = [
                "ancient stone carving",
                "ceremonial mask",
                "pottery vessel",
                "temple architecture",
                "hieroglyphic inscription",
                "ritual figurine",
                "jade artifact",
                "colossal stone head",
                "mural painting",
                "burial offering",
                "obsidian tool",
                "gold ornament",
                "stele monument",
                "ball court",
                "pyramid structure"
            ]

            # Find most similar term
            from sentence_transformers.util import cos_sim
            img_embedding = self.clip_model.encode(img)
            term_embeddings = self.clip_model.encode(cultural_terms)
            similarities = cos_sim(img_embedding, term_embeddings)[0]
            best_term_idx = similarities.argmax().item()

            metadata = self.image_metadata.get(image_path, {})
            cultural_context = metadata.get("cultural_context", ["unknown"])
            context_str = cultural_context[0] if isinstance(cultural_context, list) else cultural_context

            return f"A {cultural_terms[best_term_idx]} from {context_str} context"

        except Exception as e:
            return f"Image: {Path(image_path).name}"

    async def analyze_cultural_context(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze cultural context of an image using GLM-4V if available
        """
        metadata = self.image_metadata.get(image_path, {})

        # Use GLM-4V for enhanced analysis if available
        if self.glm_enabled:
            try:
                glm_analysis = await self._analyze_with_glm(image_path)
                return {**metadata, **glm_analysis}
            except Exception as e:
                print(f"GLM-4V analysis failed: {e}")

        # Fallback to metadata-based analysis
        return {
            "cultural_context": metadata.get("cultural_context", ["unknown"]),
            "perspective": metadata.get("perspective", "unknown"),
            "institution": metadata.get("institution", "unknown"),
            "date": metadata.get("date", "unknown"),
            "potential_biases": self._detect_potential_biases(metadata),
            "analysis_method": "metadata_only"
        }

    async def _analyze_with_glm(self, image_path: str) -> Dict[str, Any]:
        """Analyze image using GLM-4V"""
        client = self._get_glm_client()

        # Encode image
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        ext = Path(image_path).suffix.lower()
        mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"

        # Analyze with GLM-4V
        response = client.chat.completions.create(
            model="glm-4v",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this cultural heritage image and provide:\n1. Cultural origin/period (e.g., Olmec, Maya, Aztec, Unknown)\n2. Artifact type (e.g., sculpture, pottery, architecture)\n3. Key visual characteristics\n4. Notable cultural or historical significance\n\nFormat your response as structured text."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.5,
            max_tokens=400
        )

        analysis_text = response.choices[0].message.content

        return {
            "glm_analysis": analysis_text,
            "cultural_context": self._extract_cultural_context(analysis_text),
            "analysis_method": "glm-4v"
        }

    def _extract_cultural_context(self, analysis_text: str) -> List[str]:
        """Extract cultural context from GLM analysis"""
        text_lower = analysis_text.lower()
        contexts = []

        context_keywords = {
            "olmec": "Olmec",
            "maya": "Maya",
            "aztec": "Aztec",
            "mixtec": "Mixtec",
            "zapotec": "Zapotec",
            "teotihuacan": "Teotihuacan",
            "toltec": "Toltec",
            "mesoamerican": "Mesoamerican",
            "pre-columbian": "Pre-Columbian"
        }

        for keyword, context in context_keywords.items():
            if keyword in text_lower:
                contexts.append(context)

        return contexts if contexts else ["unknown"]

    def _detect_potential_biases(self, metadata: Dict) -> List[str]:
        """Detect potential biases in image metadata"""
        biases = []

        if metadata.get("perspective") == "colonial":
            biases.append("colonial_perspective")
        if metadata.get("institution", "").lower() == "western":
            biases.append("western_institution")

        cultural_context = metadata.get("cultural_context", [])
        if isinstance(cultural_context, str):
            cultural_context = [cultural_context]

        if not any("indigenous" in str(c).lower() for c in cultural_context):
            if not any(i in str(cultural_context).lower() for i in ["olmec", "maya", "aztec", "mixtec", "zapotec"]):
                biases.append("potential_indigenous_underrepresentation")

        return biases if biases else ["none_detected"]

    async def add_image(self, image_path: str, metadata: Dict = None):
        """Add new image to the vector store"""
        try:
            img = Image.open(image_path).convert("RGB")

            # Resize if needed
            max_size = self.config["vision"]["max_image_size"]
            if img.size != tuple(max_size):
                img = img.resize(max_size, Image.Resampling.LANCZOS)

            # Generate CLIP embedding
            embedding = self.clip_model.encode(img)

            # Add to cache
            self.image_paths.append(image_path)
            if len(self.image_embeddings) == 0:
                self.image_embeddings = embedding.reshape(1, -1)
            else:
                self.image_embeddings = np.vstack([self.image_embeddings, embedding])

            # Generate enhanced caption with GLM-4V if available
            caption = await self.generate_caption(image_path)

            # Update metadata
            if metadata:
                self.image_metadata[image_path] = {
                    **metadata,
                    "caption": caption
                }

                # Add GLM-4V analysis if enabled
                if self.glm_enabled:
                    try:
                        analysis = await self._analyze_with_glm(image_path)
                        self.image_metadata[image_path].update(analysis)
                    except Exception as e:
                        print(f"GLM analysis failed for {image_path}: {e}")

            # Save cache
            self._save_caches()

            # Index to Qdrant for cross-researcher searchability
            qdrant_success = self.index_image_to_qdrant(image_path, embedding, metadata)
            if qdrant_success:
                print(f"  ✓ Indexed to Qdrant: {Path(image_path).name}")

        except Exception as e:
            print(f"Error adding image {image_path}: {e}")

    def _load_embeddings_cache(self) -> tuple:
        """Load cached image embeddings"""
        cache_file = self.cache_dir / "embeddings.pkl"
        if cache_file.exists():
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        return [], np.array([])

    def _load_metadata_cache(self) -> Dict:
        """Load cached image metadata"""
        import json
        metadata_file = self.cache_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                return json.load(f)
        return {}

    def _save_caches(self):
        """Save embeddings and metadata to cache"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Save embeddings
        cache_file = self.cache_dir / "embeddings.pkl"
        with open(cache_file, "wb") as f:
            pickle.dump((self.image_paths, self.image_embeddings), f)

        # Save metadata
        import json
        metadata_file = self.cache_dir / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(self.image_metadata, f, indent=2)

    def index_image_to_qdrant(self, image_path: str, embedding: np.ndarray, metadata: Dict = None):
        """Index image to Qdrant vector store for cross-researcher searchability"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import PointStruct, VectorParams, Distance
            import hashlib
            import os

            # Get Qdrant configuration - check multiple locations
            qdrant_config = self.config.get("qdrant", {})
            if not qdrant_config:
                # Try vector_db.text.qdrant path
                vector_db_config = self.config.get("vector_db", {})
                text_config = vector_db_config.get("text", {})
                qdrant_config = text_config.get("qdrant", {})

            qdrant_url = qdrant_config.get("url", "http://localhost:6333")
            # Override with environment variable if set (for Docker)
            qdrant_url = os.getenv("QDRANT_URL", qdrant_url)
            # Convert localhost to qdrant for Docker networking
            if "localhost" in qdrant_url:
                qdrant_url = qdrant_url.replace("localhost", "qdrant")

            collection_name = self.config.get("multimodal", {}).get("vision", {}).get("image_collection", "heritage_lens_images")

            # Connect to Qdrant
            qdrant = QdrantClient(url=qdrant_url)

            # Create collection if not exists
            try:
                qdrant.get_collection(collection_name)
            except Exception:
                qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=512,  # CLIP embedding size
                        distance=Distance.COSINE
                    )
                )
                print(f"  Created Qdrant collection: {collection_name}")

            # Generate unique point ID from image path
            image_hash = hashlib.md5(image_path.encode()).hexdigest()
            point_id = int(image_hash[:16], 16)

            # Prepare payload
            payload = {
                "path": image_path,
                "source": metadata.get("source", "unknown") if metadata else "unknown",
                "page": metadata.get("page", 0) if metadata else 0,
                **({k: v for k, v in metadata.items() if k not in ["path", "source", "page"]} if metadata else {})
            }

            # Upsert to Qdrant
            qdrant.upsert(
                collection_name=collection_name,
                points=[PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=payload
                )]
            )

            return True

        except Exception as e:
            print(f"  Warning: Could not index image to Qdrant: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get vision agent statistics"""
        return {
            "images_indexed": len(self.image_paths),
            "embeddings_shape": self.image_embeddings.shape if len(self.image_embeddings) > 0 else (0,),
            "glm_enabled": self.glm_enabled,
            "cache_dir": str(self.cache_dir),
            "clip_model": self.config["vision"]["model"],
            "similarity_threshold": self.similarity_threshold
        }

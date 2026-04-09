"""
Enhanced Multimodal Orchestrator
Coordinates all sub-agents to produce 3-layer multimodal output
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import json

# Detect project root - works in Docker, local, and OpenClaw environments
if Path("/app").exists():
    PROJECT_ROOT = Path("/app")
elif (Path("/home/heritage") / "heritage-lens-multimodal").exists():
    PROJECT_ROOT = Path("/home/heritage") / "heritage-lens-multimodal"
else:
    PROJECT_ROOT = Path.home() / "heritage-lens-multimodal"

# Import conversation store
import sys
sys.path.append(str(PROJECT_ROOT))
from utils.conversation_store import ConversationStore


class EnhancedOrchestrator:
    def __init__(self, config_path: str = "config/settings.yaml"):
        config_full_path = Path(config_path)
        if not config_full_path.is_absolute():
            config_full_path = PROJECT_ROOT / config_path

        with open(config_full_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.config_path = str(config_full_path)

        # Import sub-agents
        import sys
        sys.path.append(str(PROJECT_ROOT))

        from agents.retrieval.multimodal_retrieval_agent import MultimodalRetrievalAgent
        from agents.synthesis.multimodal_synthesis_agent import MultimodalSynthesisAgent
        from agents.epistemic.enhanced_epistemic_agent import EnhancedEpistemicAgent
        from agents.critic.multimodal_critic_agent import MultimodalCriticAgent
        from agents.vision.vision_agent import VisionAgent

        # Initialize sub-agents
        self.retrieval_agent = MultimodalRetrievalAgent(self.config_path)
        self.synthesis_agent = MultimodalSynthesisAgent(self.config_path)
        self.epistemic_agent = EnhancedEpistemicAgent(self.config_path)
        self.critic_agent = MultimodalCriticAgent(self.config_path)
        self.vision_agent = VisionAgent(self.config_path)

        # Conversation history per session - now backed by persistent storage
        self.conversation_store = ConversationStore()
        # In-memory cache for performance (synced with DB)
        self._history_cache: Dict[str, List[Dict]] = {}

    async def process_query(
        self,
        query: str,
        session_id: str = "default",
        top_k_text: int = None,
        top_k_images: int = None,
        strict_corpus: bool = True,
        document_scope: List[str] = None
    ) -> Dict[str, Any]:
        """
        Process a query through the complete multimodal pipeline

        Args:
            query: User query
            session_id: Session identifier for conversation history
            top_k_text: Number of text chunks to retrieve
            top_k_images: Number of images to retrieve
            strict_corpus: If True, answer only from corpus. If False, allow general knowledge.
            document_scope: Optional list of document IDs/filenames to scope retrieval to

        Returns:
            Complete 3-layer response with all metadata
        """
        start_time = time.time()
        revision_count = 0
        max_revisions = self.config["orchestrator"].get("max_revisions", 1)

        # Get conversation history from persistent storage
        history = self._get_history(session_id)

        # Main processing loop with revision support
        while revision_count <= max_revisions:
            # Step 1: Retrieval (with optional document scoping)
            retrieval_results = await self.retrieval_agent.retrieve(
                query=query,
                top_k_text=top_k_text,
                top_k_images=top_k_images,
                document_scope=document_scope
            )

            text_chunks = retrieval_results["text_chunks"]
            images = retrieval_results["images"]

            # Step 2: Synthesis (Layer 1 & 2)
            synthesis_result = await self.synthesis_agent.synthesize(
                query=query,
                text_chunks=text_chunks,
                images=images,
                conversation_history=history,
                strict_corpus=strict_corpus
            )

            l1_answer = synthesis_result["l1_answer"]
            l2_attribution = synthesis_result["l2_attribution"]

            # Step 3: Epistemic Analysis (Layer 3)
            epistemic_result = await self.epistemic_agent.analyze(
                query=query,
                l1_answer=l1_answer,
                l2_attribution=l2_attribution,
                text_chunks=text_chunks,
                images=images,
                conversation_history=history
            )

            l3_epistemic = epistemic_result["l3_epistemic"]

            # Step 4: Critic Evaluation
            critique = await self.critic_agent.evaluate(
                query=query,
                l1_answer=l1_answer,
                l2_attribution=l2_attribution,
                l3_epistemic=l3_epistemic,
                retrieved_images=images,
                retrieval_stats=retrieval_results["stats"],
                revision_count=revision_count
            )

            # Check if revision is needed
            if not critique["revision_required"] or revision_count >= max_revisions:
                break

            # Determine revision strategy
            strategy = self.critic_agent.determine_revision_strategy(critique)

            # Apply adjustments for re-retrieval
            if strategy["action"] == "re_retrieve":
                if strategy.get("adjustments", {}).get("increase_top_k"):
                    top_k_text = (top_k_text or self.config["retrieval"]["text"]["top_k"]) + 2
                    top_k_images = (top_k_images or self.config["retrieval"]["image"]["top_k"]) + 1
                if strategy.get("adjustments", {}).get("relax_thresholds"):
                    # Note: threshold adjustment would need to be passed to agents
                    pass

            revision_count += 1

        # Update conversation history (persist to database)
        self._update_history(session_id, query, l1_answer, {
            "layers": {
                "l2_attribution": l2_attribution,
                "l3_epistemic": l3_epistemic
            },
            "retrieval_stats": retrieval_results["stats"],
            "document_scope": document_scope,
            "revisions": revision_count,
            "processing_time": time.time() - start_time
        })

        # Calculate processing time
        processing_time = time.time() - start_time

        # Build final response
        return {
            "query": query,
            "session_id": session_id,
            "layers": {
                "l1_answer": l1_answer,
                "l2_attribution": l2_attribution,
                "l3_epistemic": l3_epistemic
            },
            "retrieval": {
                "text_chunks": text_chunks,
                "images": images,
                "stats": retrieval_results["stats"],
                "document_scope": document_scope
            },
            "critique": critique,
            "revisions": revision_count,
            "processing_time": processing_time,
            "formatted_output": self._format_output(
                l1_answer, l2_attribution, l3_epistemic, images
            )
        }

    def _get_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Get conversation history from persistent storage (with caching)"""
        # Check cache first
        if session_id in self._history_cache:
            return self._history_cache[session_id]

        # Load from database
        history = self.conversation_store.get_history(session_id, limit=limit)
        self._history_cache[session_id] = history
        return history

    def _update_history(self, session_id: str, query: str, answer: str, metadata: Dict = None):
        """Update conversation history in persistent storage"""
        # Add to database
        self.conversation_store.add_message(session_id, "user", query)
        self.conversation_store.add_message(session_id, "assistant", answer, metadata)

        # Update cache
        if session_id not in self._history_cache:
            self._history_cache[session_id] = []

        self._history_cache[session_id].append({
            "role": "user",
            "content": query
        })
        self._history_cache[session_id].append({
            "role": "assistant",
            "content": answer
        })

        # Keep last 10 exchanges in cache
        max_history = 20
        if len(self._history_cache[session_id]) > max_history:
            self._history_cache[session_id] = self._history_cache[session_id][-max_history:]

    def _format_output(
        self,
        l1_answer: str,
        l2_attribution: Dict[str, Any],
        l3_epistemic: Dict[str, Any],
        images: List[Dict[str, Any]]
    ) -> str:
        """Format the complete 3-layer output for display"""
        output = []

        # Layer 1
        output.append("## Layer 1: Answer")
        output.append("")
        output.append(l1_answer)
        output.append("")

        # Layer 2
        output.append("## Layer 2: Source Attribution")
        output.append("")

        if l2_attribution.get("text_sources"):
            output.append("**Text Sources:**")
            for src in l2_attribution["text_sources"]:
                ref = src.get("reference", "")
                source = src.get("source", "unknown")
                page = src.get("page")
                page_str = f", p.{page}" if page else ""
                output.append(f"- {ref} {source}{page_str}")
            output.append("")

        if l2_attribution.get("image_sources"):
            output.append("**Image Sources:**")
            for img in l2_attribution["image_sources"]:
                ref = img.get("reference", "")
                caption = img.get("caption", "Image")
                output.append(f"- {ref} {caption}")
            output.append("")

        # Layer 3
        output.append("## Layer 3: Epistemic Transparency")
        output.append("")

        if l3_epistemic.get("textual_analysis"):
            output.append("**Textual Analysis:**")
            output.append(l3_epistemic["textual_analysis"])
            output.append("")

        if l3_epistemic.get("visual_analysis"):
            output.append("**Visual Analysis:**")
            output.append(l3_epistemic["visual_analysis"])
            output.append("")

        if l3_epistemic.get("overall_assessment"):
            output.append("**Overall Assessment:**")
            output.append(l3_epistemic["overall_assessment"])

        return "\n".join(output)

    async def add_document(self, pdf_path: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Add a PDF document to the knowledge base
        (Requires data pipeline - placeholder)
        """
        return {
            "status": "not_implemented",
            "message": "Data pipeline integration required for PDF ingestion",
            "pdf_path": pdf_path,
            "metadata": metadata
        }

    async def add_image(self, image_path: str, metadata: Dict = None) -> Dict[str, Any]:
        """Add an image to the knowledge base"""
        try:
            result = await self.vision_agent.add_image(image_path, metadata)
            return {
                "status": "success",
                "message": f"Image added successfully: {image_path}",
                "image_path": image_path,
                "metadata": metadata
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to add image: {str(e)}",
                "image_path": image_path
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        conv_stats = self.conversation_store.get_stats()
        return {
            "images_indexed": len(self.vision_agent.image_paths),
            "embedding_cache_size": len(self.vision_agent.image_paths),
            "sessions_total": conv_stats["sessions"],
            "messages_total": conv_stats["messages"],
            "config": {
                "max_revisions": self.config["orchestrator"].get("max_revisions", 1),
                "text_top_k": self.config["retrieval"]["text"]["top_k"],
                "image_top_k": self.config["retrieval"]["image"]["top_k"]
            }
        }


# Convenience function for direct usage
async def process_query(query: str, **kwargs) -> Dict[str, Any]:
    """Process a query using the default orchestrator"""
    orchestrator = EnhancedOrchestrator()
    return await orchestrator.process_query(query, **kwargs)

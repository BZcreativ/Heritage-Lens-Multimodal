"""
Multimodal Synthesis Sub-Agent
Generates Layer 1 (Answer) and Layer 2 (Attribution) with image context
"""

import asyncio
from typing import Dict, Any, List
from pathlib import Path
import yaml
import json

# Detect project root - works in both Docker and local environments
if Path("/app").exists():
    PROJECT_ROOT = Path("/app")
elif (Path("/home/heritage") / "heritage-lens-multimodal").exists():
    PROJECT_ROOT = Path("/home/heritage") / "heritage-lens-multimodal"
else:
    PROJECT_ROOT = Path.home() / "heritage-lens-multimodal"


class MultimodalSynthesisAgent:
    def __init__(self, config_path: str = "config/settings.yaml"):
        config_full_path = Path(config_path)
        if not config_full_path.is_absolute():
            config_full_path = PROJECT_ROOT / config_path

        with open(config_full_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Load prompts
        prompts_path = config_full_path.parent / "prompts.yaml"
        with open(prompts_path, "r") as f:
            self.prompts = yaml.safe_load(f)

        # LLM client will be initialized on first use
        self._llm_client = None

    def _get_llm_client(self):
        """Get configured OpenAI client"""
        from openai import OpenAI
        api_key, base_url = self._get_api_config()
        return OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)

    def _get_api_config(self) -> tuple:
        """Get API key and base URL from environment or config"""
        import os

        # Try .env file first for explicit configuration
        env_path = PROJECT_ROOT / "config" / ".env"
        env_vars = {}
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, val = line.split("=", 1)
                        env_vars[key.strip()] = val.strip()

        # Check for OpenRouter first (preferred)
        if "OPENROUTER_API_KEY" in env_vars:
            return env_vars["OPENROUTER_API_KEY"], "https://openrouter.ai/api/v1"
        if os.getenv("OPENROUTER_API_KEY"):
            return os.getenv("OPENROUTER_API_KEY"), "https://openrouter.ai/api/v1"

        # Fall back to OpenAI
        if "OPENAI_API_KEY" in env_vars:
            return env_vars["OPENAI_API_KEY"], None
        if os.getenv("OPENAI_API_KEY"):
            return os.getenv("OPENAI_API_KEY"), None

        return "", None

    async def synthesize(
        self,
        query: str,
        text_chunks: List[Dict[str, Any]],
        images: List[Dict[str, Any]],
        conversation_history: List[Dict] = None,
        strict_corpus: bool = True
    ) -> Dict[str, Any]:
        """
        Synthesize multimodal response with Layer 1 and Layer 2

        Args:
            query: User query
            text_chunks: Retrieved text chunks
            images: Retrieved images with metadata
            conversation_history: Optional conversation context
            strict_corpus: If True, answer only from corpus context

        Returns:
            Dict with l1_answer, l2_attribution, combined_output
        """
        # Build context strings
        text_context = self._format_text_context(text_chunks)
        image_context = self._format_image_context(images)

        # Check if we have sufficient context in strict mode
        has_text = text_chunks and len(text_chunks) > 0
        has_images = images and len(images) > 0
        insufficient_context = not (has_text or has_images)

        # Handle strict corpus mode with insufficient context
        if strict_corpus and insufficient_context:
            return {
                "l1_answer": "The available documents do not contain sufficient information to answer this query. Please upload relevant documents or disable strict corpus-only mode.",
                "l2_attribution": {
                    "text_sources": [],
                    "image_sources": [],
                    "disclaimer": "No relevant sources found in corpus."
                },
                "combined_output": "## Layer 1: Answer\n\nThe available documents do not contain sufficient information to answer this query.\n\n## Layer 2: Source Attribution\n\nNo relevant sources found in corpus.",
                "sources_used": 0,
                "images_used": 0
            }

        # Get LLM config
        llm_config = self.config["llm"]["synthesis"]

        # Prepare system and user prompts
        system_prompt = self.prompts["synthesis"]["system"]

        # Add strict corpus instruction if enabled
        if strict_corpus:
            system_prompt += "\n\nSTRICT CORPUS MODE ENABLED:\n- Answer ONLY using information from the Retrieved Text Context above\n- Every claim MUST have an inline citation like [Source X, p.Y]\n- If the context doesn't fully answer the query, acknowledge the limitations\n- NEVER use general knowledge not present in the retrieved context\n- For images: reference them naturally with citations like [Image Z]"
        else:
            system_prompt += "\n\nGENERAL KNOWLEDGE MODE:\n- Prioritize information from the Retrieved Text Context\n- You may supplement with general knowledge when corpus coverage is incomplete\n- Always cite corpus sources when used\n- Clearly distinguish between corpus-derived information and general knowledge"

        user_prompt_template = self.prompts["synthesis"]["user"]

        user_prompt = user_prompt_template.format(
            query=query,
            text_context=text_context,
            image_context=image_context
        )

        # Add conversation context if present
        if conversation_history:
            context_str = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-3:]:  # Last 3 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context_str += f"{role}: {content}\n"
            user_prompt = context_str + "\n" + user_prompt

        # Call LLM
        try:
            response = await self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                config=llm_config
            )

            # Parse the response
            result = self._parse_synthesis_output(response, text_chunks, images)
            return result

        except Exception as e:
            # Fallback response on error
            return {
                "l1_answer": f"Error generating response: {str(e)}",
                "l2_attribution": {
                    "text_sources": [],
                    "image_sources": [],
                    "disclaimer": "An error occurred during synthesis."
                },
                "combined_output": f"## Layer 1: Answer\n\nError: {str(e)}\n\n## Layer 2: Source Attribution\n\nUnable to provide sources due to synthesis error.",
                "error": str(e)
            }

    def _format_text_context(self, text_chunks: List[Dict[str, Any]]) -> str:
        """Format text chunks for prompt"""
        if not text_chunks:
            return "No text context retrieved."

        formatted = []
        for i, chunk in enumerate(text_chunks, 1):
            content = chunk.get("content", chunk.get("text", ""))
            source = chunk.get("metadata", {}).get("source", f"Source {i}")
            page = chunk.get("metadata", {}).get("page")

            ref = f"[Source {i}]"
            if source:
                ref += f" {source}"
                if page:
                    ref += f", p.{page}"

            formatted.append(f"{ref}:\n{content}\n")

        return "\n".join(formatted)

    def _format_image_context(self, images: List[Dict[str, Any]]) -> str:
        """Format image metadata for prompt"""
        if not images:
            return "No images retrieved."

        formatted = []
        for i, img in enumerate(images, 1):
            path = img.get("path", "unknown")
            caption = img.get("caption", "No caption available")
            similarity = img.get("similarity", 0)
            adjusted_score = img.get("adjusted_score")

            # Extract metadata
            metadata = img.get("metadata", {})
            source = metadata.get("source", "unknown")
            page = metadata.get("page", "unknown")
            cultural_context = metadata.get("cultural_context", [])

            formatted.append(
                f"[Image {i}]\n"
                f"  Path: {path}\n"
                f"  Caption: {caption}\n"
                f"  Source: {source}, Page: {page}\n"
                f"  Similarity Score: {similarity:.3f}"
                f"{' (Adjusted: ' + f'{adjusted_score:.3f}' + ')' if adjusted_score else ''}\n"
                f"  Cultural Context: {', '.join(cultural_context) if cultural_context else 'N/A'}\n"
            )

        return "\n".join(formatted)

    async def _call_llm(self, system_prompt: str, user_prompt: str, config: Dict) -> str:
        """Call LLM with configured provider"""
        provider = config.get("provider", "openai")
        model = config.get("model", "gpt-4")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)

        # Map model names for OpenRouter
        api_key, base_url = self._get_api_config()
        if base_url and "openrouter" in base_url:
            # Use OpenRouter model format
            model_map = {
                "gpt-4": "openai/gpt-4o-mini",
                "gpt-4o": "openai/gpt-4o",
                "kimi-code": "openai/gpt-4o-mini"
            }
            model = model_map.get(model, "openai/gpt-4o-mini")

        if provider in ["openai", "kimi"]:
            # Use OpenAI-compatible API
            client = self._get_llm_client()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=self._get_anthropic_key())
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return response.content[0].text

        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _get_anthropic_key(self) -> str:
        """Get Anthropic API key"""
        import os
        return os.getenv("ANTHROPIC_API_KEY", "")

    def _parse_synthesis_output(
        self,
        response: str,
        text_chunks: List[Dict],
        images: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Parse LLM response into structured output"""

        # Extract Layer 1 (Answer)
        l1_answer = response
        if "## Layer 1:" in response:
            parts = response.split("## Layer 2:")
            l1_answer = parts[0].replace("## Layer 1:", "").replace("Answer", "").strip()

        # Extract Layer 2 (Attribution)
        l2_attribution = {
            "text_sources": [],
            "image_sources": [],
            "raw_attribution": ""
        }

        if "## Layer 2:" in response:
            l2_start = response.find("## Layer 2:")
            l2_content = response[l2_start:]

            # If there's Layer 3, stop before it
            if "## Layer 3:" in l2_content:
                l2_end = l2_content.find("## Layer 3:")
                l2_content = l2_content[:l2_end]

            l2_attribution["raw_attribution"] = l2_content.replace("## Layer 2:", "").replace("Source Attribution", "").strip()

        # Build structured source lists
        for i, chunk in enumerate(text_chunks, 1):
            l2_attribution["text_sources"].append({
                "reference": f"[Source {i}]",
                "source": chunk.get("metadata", {}).get("source", "unknown"),
                "page": chunk.get("metadata", {}).get("page"),
                "similarity": chunk.get("similarity", 0)
            })

        for i, img in enumerate(images, 1):
            l2_attribution["image_sources"].append({
                "reference": f"[Image {i}]",
                "path": img.get("path"),
                "caption": img.get("caption"),
                "source": img.get("metadata", {}).get("source"),
                "page": img.get("metadata", {}).get("page"),
                "similarity": img.get("similarity", 0),
                "adjusted_score": img.get("adjusted_score")
            })

        return {
            "l1_answer": l1_answer,
            "l2_attribution": l2_attribution,
            "combined_output": response,
            "sources_used": len(text_chunks),
            "images_used": len(images)
        }

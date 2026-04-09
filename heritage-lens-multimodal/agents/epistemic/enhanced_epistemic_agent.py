"""
Enhanced Epistemic Transparency Sub-Agent
Generates Layer 3 with visual bias analysis and cultural perspective assessment
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


class EnhancedEpistemicAgent:
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

    async def analyze(
        self,
        query: str,
        l1_answer: str,
        l2_attribution: Dict[str, Any],
        text_chunks: List[Dict[str, Any]],
        images: List[Dict[str, Any]],
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate Layer 3 epistemic transparency report with visual analysis

        Args:
            query: Original user query
            l1_answer: Layer 1 answer text
            l2_attribution: Layer 2 attribution data
            text_chunks: Retrieved text chunks
            images: Retrieved images
            conversation_history: Optional conversation context

        Returns:
            Dict with structured epistemic analysis
        """
        # Build context strings
        text_sources = self._format_text_sources(text_chunks)
        image_sources = self._format_image_sources(images)

        # Get LLM config
        llm_config = self.config["llm"]["epistemic"]

        # Prepare prompts
        system_prompt = self.prompts["epistemic"]["system"]
        user_prompt_template = self.prompts["epistemic"]["user"]

        user_prompt = user_prompt_template.format(
            query=query,
            answer=l1_answer,
            text_sources=text_sources,
            image_sources=image_sources,
            context=self._build_context(text_chunks, images)
        )

        # Call LLM
        try:
            response = await self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                config=llm_config
            )

            # Parse the response
            result = self._parse_epistemic_output(response, text_chunks, images)
            return result

        except Exception as e:
            # Fallback on error
            return self._generate_fallback_analysis(e, text_chunks, images)

    def _format_text_sources(self, text_chunks: List[Dict[str, Any]]) -> str:
        """Format text sources for epistemic analysis"""
        if not text_chunks:
            return "No text sources."

        formatted = []
        for i, chunk in enumerate(text_chunks, 1):
            metadata = chunk.get("metadata", {})
            formatted.append(
                f"[Source {i}]\n"
                f"  Source: {metadata.get('source', 'unknown')}\n"
                f"  Institution: {metadata.get('institution', 'unknown')}\n"
                f"  Date: {metadata.get('date', 'unknown')}\n"
                f"  Perspective: {metadata.get('perspective', 'unknown')}\n"
                f"  Language: {metadata.get('language', 'unknown')}\n"
            )
        return "\n".join(formatted)

    def _format_image_sources(self, images: List[Dict[str, Any]]) -> str:
        """Format image sources for epistemic analysis"""
        if not images:
            return "No image sources."

        formatted = []
        for i, img in enumerate(images, 1):
            metadata = img.get("metadata", {})
            formatted.append(
                f"[Image {i}]\n"
                f"  Path: {img.get('path', 'unknown')}\n"
                f"  Caption: {img.get('caption', 'N/A')}\n"
                f"  Source: {metadata.get('source', 'unknown')}\n"
                f"  Institution: {metadata.get('institution', 'unknown')}\n"
                f"  Cultural Context: {metadata.get('cultural_context', [])}\n"
                f"  Date Captured: {metadata.get('date', 'unknown')}\n"
            )
        return "\n".join(formatted)

    def _build_context(self, text_chunks: List[Dict], images: List[Dict]) -> str:
        """Build combined context summary"""
        context = f"Retrieved {len(text_chunks)} text chunks and {len(images)} images.\n\n"

        # Analyze temporal distribution
        dates = []
        for chunk in text_chunks:
            date = chunk.get("metadata", {}).get("date")
            if date and date != "unknown":
                dates.append(date)
        for img in images:
            date = img.get("metadata", {}).get("date")
            if date and date != "unknown":
                dates.append(date)

        if dates:
            context += f"Source date range: {min(dates)} to {max(dates)}\n"

        # Analyze cultural contexts
        cultures = set()
        for chunk in text_chunks:
            cultures.update(chunk.get("metadata", {}).get("cultural_context", []))
        for img in images:
            cultures.update(img.get("metadata", {}).get("cultural_context", []))

        if cultures:
            context += f"Cultural contexts represented: {', '.join(cultures)}\n"

        return context

    async def _call_llm(self, system_prompt: str, user_prompt: str, config: Dict) -> str:
        """Call LLM with configured provider"""
        provider = config.get("provider", "openai")
        model = config.get("model", "gpt-4")
        temperature = config.get("temperature", 0.5)
        max_tokens = config.get("max_tokens", 2000)

        # Map model names for OpenRouter
        api_key, base_url = self._get_api_config()
        if base_url and "openrouter" in base_url:
            model_map = {
                "gpt-4": "openai/gpt-4o-mini",
                "gpt-4o": "openai/gpt-4o",
                "kimi-code": "openai/gpt-4o-mini"
            }
            model = model_map.get(model, "openai/gpt-4o-mini")

        if provider in ["openai", "kimi"]:
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

    def _parse_epistemic_output(
        self,
        response: str,
        text_chunks: List[Dict],
        images: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Parse LLM epistemic response into structured output"""

        # Extract sections
        textual_analysis = self._extract_section(response, "Textual Analysis", "Visual Analysis")
        visual_analysis = self._extract_section(response, "Visual Analysis", "Overall Assessment")
        overall_assessment = self._extract_section(response, "Overall Assessment", None)

        # Calculate confidence based on source diversity
        confidence_metrics = self._calculate_confidence_metrics(text_chunks, images)

        return {
            "l3_epistemic": {
                "textual_analysis": textual_analysis,
                "visual_analysis": visual_analysis,
                "overall_assessment": overall_assessment,
                "raw_output": response
            },
            "confidence_metrics": confidence_metrics,
            "bias_flags": self._extract_bias_flags(textual_analysis, visual_analysis),
            "gaps_identified": self._extract_gaps(overall_assessment)
        }

    def _extract_section(self, text: str, section_start: str, section_end: str) -> str:
        """Extract a section from the response"""
        start_marker = f"### {section_start}"
        if start_marker not in text:
            start_marker = section_start

        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""

        start_idx += len(start_marker)

        if section_end:
            end_marker = f"### {section_end}"
            if end_marker not in text:
                end_marker = section_end
            end_idx = text.find(end_marker, start_idx)
            if end_idx == -1:
                end_idx = len(text)
        else:
            end_idx = len(text)

        return text[start_idx:end_idx].strip()

    def _calculate_confidence_metrics(
        self,
        text_chunks: List[Dict],
        images: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate confidence metrics based on source diversity"""
        # Count unique sources
        text_sources = set()
        image_sources = set()
        institutions = set()
        perspectives = set()
        cultures = set()

        for chunk in text_chunks:
            metadata = chunk.get("metadata", {})
            text_sources.add(metadata.get("source", "unknown"))
            institutions.add(metadata.get("institution", "unknown"))
            perspectives.add(metadata.get("perspective", "unknown"))
            cultures.update(metadata.get("cultural_context", []))

        for img in images:
            metadata = img.get("metadata", {})
            image_sources.add(metadata.get("source", "unknown"))
            institutions.add(metadata.get("institution", "unknown"))
            cultures.update(metadata.get("cultural_context", []))

        return {
            "unique_text_sources": len(text_sources),
            "unique_image_sources": len(image_sources),
            "unique_institutions": len(institutions),
            "perspective_diversity": len(perspectives),
            "cultural_contexts": len(cultures),
            "source_diversity_score": min(1.0, (len(text_sources) + len(image_sources)) / 5),
            "perspective_diversity_score": min(1.0, len(perspectives) / 3)
        }

    def _extract_bias_flags(self, textual_analysis: str, visual_analysis: str) -> List[str]:
        """Extract bias flags from analyses"""
        flags = []

        combined = (textual_analysis + " " + visual_analysis).lower()

        bias_indicators = {
            "colonial": "Potential colonial bias detected",
            "western": "Western-centric perspective may be present",
            "missing": "Gaps in cultural representation identified",
            "limited": "Limited source diversity",
            "outdated": "Sources may be outdated",
            "blurry": "Image quality concerns",
            "cropped": "Potentially incomplete visual context"
        }

        for keyword, flag in bias_indicators.items():
            if keyword in combined:
                flags.append(flag)

        return flags

    def _extract_gaps(self, overall_assessment: str) -> List[str]:
        """Extract identified gaps from assessment"""
        gaps = []

        # Look for common gap indicators
        if "gap" in overall_assessment.lower():
            lines = overall_assessment.split("\n")
            for line in lines:
                if "gap" in line.lower() or "missing" in line.lower() or "lack" in line.lower():
                    line = line.strip("- *•").strip()
                    if len(line) > 10:
                        gaps.append(line)

        return gaps[:5]  # Limit to top 5

    def _generate_fallback_analysis(
        self,
        error: Exception,
        text_chunks: List[Dict],
        images: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate fallback analysis on error"""
        return {
            "l3_epistemic": {
                "textual_analysis": f"Error generating textual analysis: {str(error)}",
                "visual_analysis": "Unable to analyze visual content due to error.",
                "overall_assessment": "Epistemic analysis incomplete due to processing error.",
                "raw_output": ""
            },
            "confidence_metrics": self._calculate_confidence_metrics(text_chunks, images),
            "bias_flags": ["Analysis incomplete - manual review recommended"],
            "gaps_identified": ["Unable to identify gaps due to error"],
            "error": str(error)
        }

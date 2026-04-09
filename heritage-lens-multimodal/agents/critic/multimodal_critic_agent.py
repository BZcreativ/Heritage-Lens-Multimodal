"""
Multimodal Critic Sub-Agent
Evaluates output quality and determines if revision is needed
"""

import asyncio
import json
import re
from typing import Dict, Any, List
from pathlib import Path
import yaml

# Detect project root - works in both Docker and local environments
if Path("/app").exists():
    PROJECT_ROOT = Path("/app")
elif (Path("/home/heritage") / "heritage-lens-multimodal").exists():
    PROJECT_ROOT = Path("/home/heritage") / "heritage-lens-multimodal"
else:
    PROJECT_ROOT = Path.home() / "heritage-lens-multimodal"



class MultimodalCriticAgent:
    def __init__(self, config_path: str = "config/settings.yaml"):
        config_full_path = Path(config_path)
        if not config_full_path.is_absolute():
            config_full_path = PROJECT_ROOT / config_path

        with open(config_full_path, "r") as f:
            self.config = yaml.safe_load(f)

        prompts_path = config_full_path.parent / "prompts.yaml"
        with open(prompts_path, "r") as f:
            self.prompts = yaml.safe_load(f)

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

    async def evaluate(
        self,
        query: str,
        l1_answer: str,
        l2_attribution: Dict[str, Any],
        l3_epistemic: Dict[str, Any],
        retrieved_images: List[Dict[str, Any]],
        retrieval_stats: Dict[str, Any],
        revision_count: int = 0
    ) -> Dict[str, Any]:
        """
        Evaluate the complete 3-layer output

        Returns:
            Dict with verdict, confidence, and feedback
        """
        # Check max revisions
        max_revisions = self.config["orchestrator"].get("max_revisions", 1)
        if revision_count >= max_revisions:
            return {
                "verdict": "accept",
                "confidence": 0.7,
                "feedback": f"Max revisions ({max_revisions}) reached. Accepting current output.",
                "image_feedback": "N/A - max revisions reached",
                "multimodal_coherence": 0.7,
                "revision_required": False
            }

        # Get LLM config
        llm_config = self.config["llm"]["critic"]

        # Prepare prompts
        system_prompt = self.prompts["critic"]["system"]
        user_prompt_template = self.prompts["critic"]["user"]

        user_prompt = user_prompt_template.format(
            query=query,
            l1=l1_answer,
            l2=json.dumps(l2_attribution, indent=2),
            l3=json.dumps(l3_epistemic, indent=2),
            retrieved_images=json.dumps([
                {"path": img.get("path"), "caption": img.get("caption"), "similarity": img.get("similarity")}
                for img in retrieved_images
            ], indent=2),
            retrieval_stats=json.dumps(retrieval_stats, indent=2)
        )

        # Call LLM
        try:
            response = await self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                config=llm_config
            )

            # Parse JSON response
            result = self._parse_critic_output(response)
            result["revision_required"] = result["verdict"] != "accept"
            result["revision_count"] = revision_count
            return result

        except Exception as e:
            # Fallback on error - accept with warning
            return {
                "verdict": "accept",
                "confidence": 0.5,
                "feedback": f"Critic evaluation failed: {str(e)}. Proceeding with caution.",
                "image_feedback": "Unable to evaluate images due to error",
                "multimodal_coherence": 0.5,
                "revision_required": False,
                "revision_count": revision_count,
                "error": str(e)
            }

    async def _call_llm(self, system_prompt: str, user_prompt: str, config: Dict) -> str:
        provider = config.get("provider", "openai")
        model = config.get("model", "gpt-4")
        temperature = config.get("temperature", 0.3)
        max_tokens = config.get("max_tokens", 1500)

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
        import os
        return os.getenv("ANTHROPIC_API_KEY", "")

    def _parse_critic_output(self, response: str) -> Dict[str, Any]:
        """Parse critic response, handling both JSON and markdown-wrapped JSON"""
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)

        # Try to find JSON object directly
        json_match = re.search(r'\{.*"verdict".*"confidence".*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)

        try:
            result = json.loads(response)

            # Validate required fields
            if "verdict" not in result:
                result["verdict"] = "accept"
            if "confidence" not in result:
                result["confidence"] = 0.7
            if "feedback" not in result:
                result["feedback"] = "No specific feedback provided."
            if "image_feedback" not in result:
                result["image_feedback"] = "No image feedback provided."
            if "multimodal_coherence" not in result:
                result["multimodal_coherence"] = result.get("confidence", 0.7)

            # Validate verdict value
            valid_verdicts = ["accept", "revise_retrieval", "revise_synthesis", "revise_epistemic", "revise_vision"]
            if result["verdict"] not in valid_verdicts:
                result["verdict"] = "accept"

            # Ensure confidence is in valid range
            result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
            result["multimodal_coherence"] = max(0.0, min(1.0, float(result["multimodal_coherence"])))

            return result

        except json.JSONDecodeError:
            # Fallback parsing from text
            return self._fallback_parse_critic_response(response)

    def _fallback_parse_critic_response(self, response: str) -> Dict[str, Any]:
        """Fallback parsing when JSON is not valid"""
        response_lower = response.lower()

        # Determine verdict from text
        if "revise_retrieval" in response_lower or "retrieval" in response_lower and "revise" in response_lower:
            verdict = "revise_retrieval"
        elif "revise_synthesis" in response_lower or "synthesis" in response_lower and "revise" in response_lower:
            verdict = "revise_synthesis"
        elif "revise_epistemic" in response_lower or "epistemic" in response_lower and "revise" in response_lower:
            verdict = "revise_epistemic"
        elif "revise_vision" in response_lower or "vision" in response_lower and "revise" in response_lower:
            verdict = "revise_vision"
        elif "accept" in response_lower:
            verdict = "accept"
        else:
            verdict = "accept"  # Default to accept

        # Extract confidence
        confidence_match = re.search(r'confidence[:\s]+(\d+\.?\d*)', response_lower)
        confidence = float(confidence_match.group(1)) if confidence_match else 0.7
        confidence = max(0.0, min(1.0, confidence))

        # Extract coherence
        coherence_match = re.search(r'coherence[:\s]+(\d+\.?\d*)', response_lower)
        coherence = float(coherence_match.group(1)) if coherence_match else confidence
        coherence = max(0.0, min(1.0, coherence))

        return {
            "verdict": verdict,
            "confidence": confidence,
            "feedback": response[:500] + "..." if len(response) > 500 else response,
            "image_feedback": "Parsed from text - no separate image feedback available",
            "multimodal_coherence": coherence,
            "parsed_fallback": True
        }

    def determine_revision_strategy(self, critique: Dict[str, Any]) -> Dict[str, Any]:
        """Determine what needs to be revised based on critique"""
        verdict = critique.get("verdict", "accept")

        strategies = {
            "accept": {
                "action": "none",
                "target_agent": None,
                "message": "Output accepted, no revision needed"
            },
            "revise_retrieval": {
                "action": "re_retrieve",
                "target_agent": "retrieval",
                "message": "Retrieval needs improvement - adjusting parameters",
                "adjustments": {
                    "increase_top_k": True,
                    "relax_thresholds": True
                }
            },
            "revise_synthesis": {
                "action": "re_synthesize",
                "target_agent": "synthesis",
                "message": "Synthesis needs improvement - regenerating with feedback",
                "feedback": critique.get("feedback", "")
            },
            "revise_epistemic": {
                "action": "re_analyze",
                "target_agent": "epistemic",
                "message": "Epistemic analysis needs improvement",
                "feedback": critique.get("feedback", "")
            },
            "revise_vision": {
                "action": "re_search_images",
                "target_agent": "vision",
                "message": "Image search needs improvement - adjusting parameters",
                "adjustments": {
                    "increase_top_k": True,
                    "lower_threshold": True
                }
            }
        }

        return strategies.get(verdict, strategies["accept"])

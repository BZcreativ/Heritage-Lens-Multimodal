"""Load environment variables from config/.env by absolute path.

In production the systemd unit (heritage-streamlit.service) loads config/.env via
EnvironmentFile=. On the host there is no root .env, so a bare load_dotenv() finds
nothing and API keys silently go missing. Resolving config/.env relative to this
file makes host runs (scripts, tests, ad-hoc `python agent/...`) pick up the keys too.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

_CONFIG_ENV = Path(__file__).resolve().parent.parent / "config" / ".env"

_DEFAULT_LLM_MODEL = "openai/gpt-5.6-luna-pro"


def load_env(override: bool = True) -> None:
    """Load config/.env into the process environment."""
    load_dotenv(_CONFIG_ENV, override=override)


def get_llm_model() -> str:
    """OpenRouter model id for text LLM calls (synthesis, judge)."""
    return os.getenv("OPENAI_MODEL", _DEFAULT_LLM_MODEL)


def get_llm_vision_model() -> str:
    """OpenRouter model id for vision calls; falls back to the text model."""
    return os.getenv("OPENAI_VISION_MODEL") or get_llm_model()

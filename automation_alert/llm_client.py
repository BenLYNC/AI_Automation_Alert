"""Provider-agnostic LLM client.

Supports multiple LLM providers through a unified interface.
The scorer doesn't need to know which provider is being used.

Supported providers:
- anthropic: Claude models (requires ANTHROPIC_API_KEY)
- gemini: Google Gemini models (requires GEMINI_API_KEY)
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract base for LLM provider clients."""

    @abstractmethod
    def call(self, system: str, user_prompt: str) -> str:
        """Send a system + user prompt and return the text response."""

    def parse_json_array(self, text: str) -> list[dict[str, Any]]:
        """Extract a JSON array from an LLM response."""
        text = text.strip()
        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError(f"No JSON array found in LLM response: {text[:200]}")

        return json.loads(text[start:end])


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------

class AnthropicClient(LLMClient):
    """Claude via the Anthropic API."""

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-5-20250929"):
        import anthropic

        self.model = model
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
        )

    def call(self, system: str, user_prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text


# ---------------------------------------------------------------------------
# Google Gemini
# ---------------------------------------------------------------------------

class GeminiClient(LLMClient):
    """Google Gemini via the google-genai SDK."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.0-flash"):
        from google import genai

        key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        self.model = model
        self.client = genai.Client(api_key=key)

    def call(self, system: str, user_prompt: str) -> str:
        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=8192,
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        return response.text


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

# Default models per provider
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-5-20250929",
    "gemini": "gemini-2.0-flash",
}

# Available models per provider (for help text)
AVAILABLE_MODELS: dict[str, list[str]] = {
    "anthropic": [
        "claude-sonnet-4-5-20250929",
        "claude-haiku-4-5-20251001",
        "claude-opus-4-6",
    ],
    "gemini": [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ],
}


def create_client(
    provider: str = "gemini",
    model: str | None = None,
    api_key: str | None = None,
) -> LLMClient:
    """Create an LLM client for the given provider.

    Args:
        provider: "anthropic" or "gemini"
        model: Model name (uses provider default if not specified)
        api_key: API key (falls back to environment variables)
    """
    model = model or DEFAULT_MODELS.get(provider, "")

    if provider == "anthropic":
        return AnthropicClient(api_key=api_key, model=model)
    elif provider == "gemini":
        return GeminiClient(api_key=api_key, model=model)
    else:
        raise ValueError(
            f"Unknown provider: {provider}. Supported: anthropic, gemini"
        )

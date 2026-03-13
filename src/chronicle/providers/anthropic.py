"""Anthropic Claude provider for chronicle-ai."""

import os

from .base import BaseProvider, ProviderError

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class AnthropicProvider(BaseProvider):
    """Uses the Anthropic API (Claude models)."""

    def __init__(self, model: str = None):
        self._model = model or DEFAULT_MODEL
        self._api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    @property
    def name(self) -> str:
        return f"claude ({self._model})"

    def complete(self, prompt: str, system: str = "") -> str:
        try:
            import anthropic
        except ImportError as e:
            raise ProviderError(
                "anthropic package not installed. Run: pip install 'chronicle-ai[anthropic]'"
            ) from e

        if not self._api_key:
            raise ProviderError(
                "ANTHROPIC_API_KEY not set. Export it or use --provider ollama."
            )

        try:
            client = anthropic.Anthropic(api_key=self._api_key)
            messages = [{"role": "user", "content": prompt}]
            kwargs = {
                "model": self._model,
                "max_tokens": 2048,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system

            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            raise ProviderError(f"Anthropic API error: {e}") from e

"""OpenAI provider for chronicle-ai."""

import os

from .base import BaseProvider, ProviderError

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(BaseProvider):
    """Uses the OpenAI API."""

    def __init__(self, model: str = None):
        self._model = model or DEFAULT_MODEL
        self._api_key = os.environ.get("OPENAI_API_KEY", "")

    @property
    def name(self) -> str:
        return f"openai ({self._model})"

    def complete(self, prompt: str, system: str = "") -> str:
        try:
            import openai
        except ImportError as e:
            raise ProviderError(
                "openai package not installed. Run: pip install 'chronicle-ai[openai]'"
            ) from e

        if not self._api_key:
            raise ProviderError(
                "OPENAI_API_KEY not set. Export it or use --provider ollama."
            )

        try:
            client = openai.OpenAI(api_key=self._api_key)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_completion_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ProviderError(f"OpenAI API error: {e}") from e

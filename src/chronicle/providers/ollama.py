"""Ollama (local LLM) provider for chronicle-ai."""

import httpx

from .base import BaseProvider, ProviderError

DEFAULT_MODEL = "llama3.2"
OLLAMA_BASE_URL = "http://localhost:11434"


class OllamaProvider(BaseProvider):
    """Uses a local Ollama instance."""

    def __init__(self, model: str = None, base_url: str = OLLAMA_BASE_URL):
        self._model = model or DEFAULT_MODEL
        self._base_url = base_url

    @property
    def name(self) -> str:
        return f"ollama ({self._model})"

    def complete(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = httpx.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": messages,
                    "stream": False,
                },
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except httpx.ConnectError as e:
            raise ProviderError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            ) from e
        except Exception as e:
            raise ProviderError(f"Ollama error: {e}") from e

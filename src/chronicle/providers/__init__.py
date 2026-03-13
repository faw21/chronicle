"""LLM provider implementations for chronicle-ai."""

from .base import BaseProvider, ProviderError
from .ollama import OllamaProvider

__all__ = ["BaseProvider", "ProviderError", "OllamaProvider", "get_provider"]


def get_provider(provider: str, model: str = None) -> "BaseProvider":
    """Factory: return the appropriate provider instance."""
    provider = provider.lower()

    if provider in ("claude", "anthropic"):
        from .anthropic import AnthropicProvider
        return AnthropicProvider(model=model)
    elif provider in ("openai", "gpt"):
        from .openai import OpenAIProvider
        return OpenAIProvider(model=model)
    elif provider == "ollama":
        return OllamaProvider(model=model)
    else:
        raise ValueError(
            f"Unknown provider '{provider}'. Choose from: claude, openai, ollama"
        )

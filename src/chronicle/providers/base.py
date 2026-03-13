"""Base provider interface for chronicle-ai."""

from abc import ABC, abstractmethod


class ProviderError(Exception):
    """Raised when an LLM provider call fails."""


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def complete(self, prompt: str, system: str = "") -> str:
        """Send a prompt and return the completion text."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""

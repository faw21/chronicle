"""Tests for chronicle.providers."""

from unittest.mock import MagicMock, patch

import pytest

from chronicle.providers import get_provider
from chronicle.providers.base import BaseProvider, ProviderError
from chronicle.providers.ollama import OllamaProvider


class TestGetProvider:
    def test_claude_provider(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = get_provider("claude")
        assert "claude" in provider.name

    def test_anthropic_alias(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = get_provider("anthropic")
        assert "claude" in provider.name

    def test_openai_provider(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = get_provider("openai")
        assert "openai" in provider.name

    def test_gpt_alias(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = get_provider("gpt")
        assert "openai" in provider.name

    def test_ollama_provider(self):
        provider = get_provider("ollama")
        assert "ollama" in provider.name

    def test_invalid_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("unknown_provider")

    def test_model_override(self):
        provider = get_provider("ollama", model="mistral")
        assert "mistral" in provider.name


class TestOllamaProvider:
    def test_name_includes_model(self):
        provider = OllamaProvider(model="llama3.2")
        assert "llama3.2" in provider.name

    def test_default_model(self):
        provider = OllamaProvider()
        assert "llama3.2" in provider.name

    def test_complete_success(self):
        provider = OllamaProvider()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Generated story about the code."}
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.post", return_value=mock_response) as mock_post:
            result = provider.complete("Tell me a story", system="You are helpful.")

        assert result == "Generated story about the code."
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["model"] == "llama3.2"
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"

    def test_complete_without_system(self):
        provider = OllamaProvider()
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Story"}}
        mock_response.raise_for_status.return_value = None

        with patch("httpx.post", return_value=mock_response) as mock_post:
            result = provider.complete("prompt only")

        payload = mock_post.call_args[1]["json"]
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"

    def test_connection_error_raises_provider_error(self):
        import httpx
        provider = OllamaProvider()
        with patch("httpx.post", side_effect=httpx.ConnectError("Connection refused")):
            with pytest.raises(ProviderError, match="Cannot connect to Ollama"):
                provider.complete("prompt")

    def test_api_error_raises_provider_error(self):
        provider = OllamaProvider()
        with patch("httpx.post", side_effect=Exception("API error")):
            with pytest.raises(ProviderError, match="Ollama error"):
                provider.complete("prompt")

    def test_custom_base_url(self):
        provider = OllamaProvider(base_url="http://remote:11434")
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "ok"}}
        mock_response.raise_for_status.return_value = None

        with patch("httpx.post", return_value=mock_response) as mock_post:
            provider.complete("test")

        assert "http://remote:11434" in mock_post.call_args[0][0]


class TestAnthropicProvider:
    def test_missing_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            from chronicle.providers.anthropic import AnthropicProvider
            provider = AnthropicProvider()
            with pytest.raises(ProviderError, match="ANTHROPIC_API_KEY"):
                provider.complete("prompt")

    def test_missing_package_raises(self):
        import sys
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            from chronicle.providers.anthropic import AnthropicProvider
            provider = AnthropicProvider()
            with patch.dict(sys.modules, {"anthropic": None}):
                with pytest.raises((ProviderError, ImportError)):
                    provider.complete("prompt")

    def test_name_includes_model(self):
        from chronicle.providers.anthropic import AnthropicProvider
        provider = AnthropicProvider(model="claude-opus-4-6")
        assert "claude-opus-4-6" in provider.name


class TestOpenAIProvider:
    def test_missing_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            from chronicle.providers.openai import OpenAIProvider
            provider = OpenAIProvider()
            with pytest.raises(ProviderError, match="OPENAI_API_KEY"):
                provider.complete("prompt")

    def test_name_includes_model(self):
        from chronicle.providers.openai import OpenAIProvider
        provider = OpenAIProvider(model="gpt-4o")
        assert "gpt-4o" in provider.name


class TestBaseProvider:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            BaseProvider()

    def test_concrete_implementation(self):
        class ConcreteProvider(BaseProvider):
            @property
            def name(self):
                return "test"

            def complete(self, prompt, system=""):
                return "response"

        provider = ConcreteProvider()
        assert provider.name == "test"
        assert provider.complete("prompt") == "response"

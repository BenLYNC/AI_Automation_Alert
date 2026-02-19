"""Tests for the provider-agnostic LLM client layer."""

from __future__ import annotations


import pytest

from automation_alert.llm_client import (
    AVAILABLE_MODELS,
    DEFAULT_MODELS,
    LLMClient,
    create_client,
)


# ---------------------------------------------------------------------------
# LLMClient.parse_json_array
# ---------------------------------------------------------------------------


class _DummyClient(LLMClient):
    def call(self, system: str, user_prompt: str) -> str:
        return "not used"


@pytest.fixture
def parser():
    return _DummyClient()


class TestParseJsonArray:
    def test_plain_json(self, parser):
        text = '[{"a": 1}, {"b": 2}]'
        result = parser.parse_json_array(text)
        assert result == [{"a": 1}, {"b": 2}]

    def test_json_with_markdown_fences(self, parser):
        text = '```json\n[{"x": 42}]\n```'
        result = parser.parse_json_array(text)
        assert result == [{"x": 42}]

    def test_json_with_surrounding_text(self, parser):
        text = 'Here is the result:\n[{"key": "val"}]\nDone.'
        result = parser.parse_json_array(text)
        assert result == [{"key": "val"}]

    def test_empty_array(self, parser):
        result = parser.parse_json_array("[]")
        assert result == []

    def test_no_json_raises(self, parser):
        with pytest.raises(ValueError, match="No JSON array"):
            parser.parse_json_array("This has no array at all.")

    def test_nested_arrays(self, parser):
        text = '[{"items": [1, 2, 3]}]'
        result = parser.parse_json_array(text)
        assert result == [{"items": [1, 2, 3]}]


# ---------------------------------------------------------------------------
# Factory: create_client
# ---------------------------------------------------------------------------


class TestCreateClient:
    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            create_client(provider="openai")

    def test_gemini_without_key_raises(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(BaseException):
            # Raises ValueError("GEMINI_API_KEY ...") when google-genai is
            # fully importable, or a pyo3 PanicException (BaseException) in
            # environments where cryptography C extensions are unavailable.
            create_client(provider="gemini")

    def test_anthropic_creates_client(self, monkeypatch):
        """AnthropicClient can be created with a dummy key (no network call)."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        client = create_client(provider="anthropic")
        assert client.model == DEFAULT_MODELS["anthropic"]

    def test_custom_model(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        client = create_client(provider="anthropic", model="claude-haiku-4-5-20251001")
        assert client.model == "claude-haiku-4-5-20251001"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_default_models_has_both_providers(self):
        assert "gemini" in DEFAULT_MODELS
        assert "anthropic" in DEFAULT_MODELS

    def test_available_models_lists_defaults(self):
        for provider, default in DEFAULT_MODELS.items():
            assert default in AVAILABLE_MODELS[provider]

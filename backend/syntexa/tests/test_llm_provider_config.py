"""Unit tests for the AG2 llm_config builder."""
from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from syntexa.core import crypto
from syntexa.llm.provider_config import build_llm_config, mask_key
from syntexa.models import LLMProvider


@pytest.fixture(autouse=True)
def _isolated_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYNTEXA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    crypto.reset_cache_for_tests()


def _provider(**overrides) -> LLMProvider:
    defaults = dict(
        id=1,
        name="p",
        provider_type="openai",
        base_url=None,
        api_key_encrypted=crypto.encrypt("sk-x"),
        default_model="gpt-4o-mini",
        is_active=True,
    )
    defaults.update(overrides)
    # Bypass SQLAlchemy session — just build an in-memory row for the test.
    p = LLMProvider()
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


def test_openai_config_shape() -> None:
    cfg = build_llm_config(_provider(provider_type="openai"))
    entry = cfg["config_list"][0]
    assert entry["api_type"] == "openai"
    assert entry["api_key"] == "sk-x"
    assert entry["model"] == "gpt-4o-mini"
    assert "base_url" not in entry  # Official OpenAI — no base_url needed.


def test_anthropic_config_shape() -> None:
    cfg = build_llm_config(
        _provider(
            provider_type="anthropic",
            api_key_encrypted=crypto.encrypt("sk-ant-foo"),
            default_model="claude-opus-4-7",
        )
    )
    entry = cfg["config_list"][0]
    assert entry["api_type"] == "anthropic"
    assert entry["api_key"] == "sk-ant-foo"
    assert entry["model"] == "claude-opus-4-7"


def test_openrouter_defaults_base_url() -> None:
    cfg = build_llm_config(
        _provider(
            provider_type="openrouter",
            base_url=None,
            api_key_encrypted=crypto.encrypt("sk-or-v1-abc"),
            default_model="openai/gpt-4o-mini",
        )
    )
    entry = cfg["config_list"][0]
    assert entry["api_type"] == "openai"  # OpenRouter speaks OpenAI wire format.
    assert entry["base_url"] == "https://openrouter.ai/api/v1"
    assert entry["api_key"] == "sk-or-v1-abc"


def test_ollama_uses_placeholder_key_when_missing() -> None:
    cfg = build_llm_config(
        _provider(
            provider_type="ollama",
            base_url=None,
            api_key_encrypted=None,
            default_model="llama3.1",
        )
    )
    entry = cfg["config_list"][0]
    assert entry["base_url"] == "http://localhost:11434/v1"
    # AG2 SDK insists on a non-empty key string; we inject a dummy.
    assert entry["api_key"] == "ollama"


def test_model_override() -> None:
    p = _provider(default_model="gpt-4o-mini")
    cfg = build_llm_config(p, model="gpt-4o")
    assert cfg["config_list"][0]["model"] == "gpt-4o"


def test_mask_key() -> None:
    assert mask_key("sk-ant-1234567890abcd") == "sk-ant…abcd"
    assert mask_key(None) is None
    assert mask_key("") is None
    # Short keys are fully masked to avoid leaking length signal.
    assert mask_key("short") == "*****"

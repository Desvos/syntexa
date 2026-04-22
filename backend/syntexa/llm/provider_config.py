"""Translate an LLMProvider row into an AG2-compatible `llm_config` dict.

AG2 (ag2>=0.11) uses the OpenAI config_list format for every backend — the
fields that change per backend are `api_type`, `base_url`, and the key
name expected in the env. For OpenAI-compatible endpoints (OpenRouter,
Ollama, generic) we pass `base_url` directly and set `api_type="openai"`.
"""
from __future__ import annotations

from typing import Any

from syntexa.core.crypto import decrypt
from syntexa.models import LLMProvider


_DEFAULT_BASE_URLS: dict[str, str] = {
    "openrouter": "https://openrouter.ai/api/v1",
    "ollama": "http://localhost:11434/v1",
}


def _decrypted_key(provider: LLMProvider) -> str | None:
    if not provider.api_key_encrypted:
        return None
    return decrypt(provider.api_key_encrypted)


def build_llm_config(provider: LLMProvider, *, model: str | None = None) -> dict[str, Any]:
    """Return an AG2 `llm_config` dict bound to this provider.

    `model` lets a caller (an Agent) override the provider's default model
    without re-registering the provider.
    """
    chosen_model = model or provider.default_model
    key = _decrypted_key(provider)
    ptype = provider.provider_type

    entry: dict[str, Any] = {"model": chosen_model}

    if ptype == "anthropic":
        entry["api_type"] = "anthropic"
        if key:
            entry["api_key"] = key
        if provider.base_url:
            entry["base_url"] = provider.base_url
    elif ptype == "openai":
        entry["api_type"] = "openai"
        if key:
            entry["api_key"] = key
        if provider.base_url:
            entry["base_url"] = provider.base_url
    else:
        # openrouter / ollama / openai_compatible — all OpenAI wire format
        entry["api_type"] = "openai"
        entry["base_url"] = provider.base_url or _DEFAULT_BASE_URLS.get(ptype, "")
        # Ollama accepts any non-empty token; use a placeholder if unset so
        # AG2's SDK stops complaining about missing auth.
        entry["api_key"] = key or ("ollama" if ptype == "ollama" else "")

    return {"config_list": [entry]}


def mask_key(key: str | None, *, keep: int = 4) -> str | None:
    """Return a UI-safe preview of an API key: first 6 + '…' + last `keep`.

    Returns None if `key` is falsy. Short keys (< 12 chars) are fully masked.
    """
    if not key:
        return None
    if len(key) < 12:
        return "*" * len(key)
    return f"{key[:6]}…{key[-keep:]}"

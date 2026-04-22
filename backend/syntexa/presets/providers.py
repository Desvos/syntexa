"""Built-in LLMProvider starter templates.

These are blueprints only — the user still supplies the API key when they
apply one. Each entry matches the shape of LLMProviderCreate minus
``api_key`` + ``is_active``.
"""
from __future__ import annotations

from typing import Any

BUILTIN_PROVIDER_PRESETS: list[dict[str, Any]] = [
    {
        "name": "claude-sonnet",
        "provider_type": "anthropic",
        "default_model": "claude-sonnet-4-6",
        "base_url": None,
        "description": "Anthropic Claude Sonnet (native API).",
    },
    {
        "name": "gpt-4",
        "provider_type": "openai",
        "default_model": "gpt-4o",
        "base_url": None,
        "description": "OpenAI GPT-4o (native API).",
    },
    {
        "name": "openrouter",
        "provider_type": "openrouter",
        "default_model": "anthropic/claude-sonnet-4",
        "base_url": "https://openrouter.ai/api/v1",
        "description": "OpenRouter multi-model gateway.",
    },
    {
        "name": "ollama",
        "provider_type": "ollama",
        "default_model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
        "description": "Local Ollama runtime (no API key required).",
    },
]

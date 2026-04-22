"""CRUD tests for /api/v1/llm-providers."""
from __future__ import annotations

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from syntexa.core import crypto


@pytest.fixture(autouse=True)
def _isolated_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYNTEXA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    crypto.reset_cache_for_tests()


def test_create_anthropic_provider(client: TestClient, auth_headers: dict) -> None:
    resp = client.post(
        "/api/v1/llm-providers",
        json={
            "name": "claude-main",
            "provider_type": "anthropic",
            "api_key": "sk-ant-supersecret-1234567890",
            "default_model": "claude-sonnet-4-5-20250929",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "claude-main"
    assert data["provider_type"] == "anthropic"
    assert data["default_model"] == "claude-sonnet-4-5-20250929"
    # Preview, not the real key.
    assert data["api_key_preview"]
    assert "supersecret" not in data["api_key_preview"]
    assert data["api_key_preview"].endswith("7890")


def test_ollama_provider_requires_no_key(client: TestClient, auth_headers: dict) -> None:
    resp = client.post(
        "/api/v1/llm-providers",
        json={
            "name": "local-ollama",
            "provider_type": "ollama",
            "default_model": "llama3.1",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["api_key_preview"] is None


def test_non_ollama_requires_key(client: TestClient, auth_headers: dict) -> None:
    resp = client.post(
        "/api/v1/llm-providers",
        json={
            "name": "keyless-openai",
            "provider_type": "openai",
            "default_model": "gpt-4o-mini",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert "api_key is required" in resp.text


def test_unknown_provider_type_rejected(client: TestClient, auth_headers: dict) -> None:
    resp = client.post(
        "/api/v1/llm-providers",
        json={
            "name": "mystery",
            "provider_type": "nonesuch",
            "api_key": "x",
            "default_model": "m",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_duplicate_name_returns_409(client: TestClient, auth_headers: dict) -> None:
    payload = {
        "name": "dup",
        "provider_type": "openrouter",
        "api_key": "sk-or-v1-abcdef",
        "default_model": "openai/gpt-4o-mini",
    }
    assert client.post("/api/v1/llm-providers", json=payload, headers=auth_headers).status_code == 201
    resp = client.post("/api/v1/llm-providers", json=payload, headers=auth_headers)
    assert resp.status_code == 409


def test_update_rotates_key_without_echoing(client: TestClient, auth_headers: dict) -> None:
    created = client.post(
        "/api/v1/llm-providers",
        json={
            "name": "rot",
            "provider_type": "openrouter",
            "api_key": "sk-or-v1-ORIGINAL-aaaaaaaa",
            "default_model": "openai/gpt-4o-mini",
        },
        headers=auth_headers,
    ).json()

    resp = client.put(
        f"/api/v1/llm-providers/{created['id']}",
        json={"api_key": "sk-or-v1-ROTATED-bbbbbbbb"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    preview = resp.json()["api_key_preview"]
    assert "ROTATED" not in preview  # masked
    assert preview.endswith("bbbb")


def test_update_without_key_keeps_stored_key(client: TestClient, auth_headers: dict) -> None:
    """A PATCH with api_key omitted must leave the stored ciphertext alone."""
    from syntexa.models import LLMProvider, session_scope

    created = client.post(
        "/api/v1/llm-providers",
        json={
            "name": "keep",
            "provider_type": "openai",
            "api_key": "sk-keep-me-please-abc",
            "default_model": "gpt-4o-mini",
        },
        headers=auth_headers,
    ).json()

    with session_scope() as s:
        original_ct = s.get(LLMProvider, created["id"]).api_key_encrypted

    resp = client.put(
        f"/api/v1/llm-providers/{created['id']}",
        json={"default_model": "gpt-4o"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["default_model"] == "gpt-4o"

    with session_scope() as s:
        assert s.get(LLMProvider, created["id"]).api_key_encrypted == original_ct


def test_delete_provider(client: TestClient, auth_headers: dict) -> None:
    created = client.post(
        "/api/v1/llm-providers",
        json={
            "name": "gone",
            "provider_type": "ollama",
            "default_model": "llama3.1",
        },
        headers=auth_headers,
    ).json()
    resp = client.delete(f"/api/v1/llm-providers/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204

    listing = client.get("/api/v1/llm-providers", headers=auth_headers).json()
    assert all(p["id"] != created["id"] for p in listing["providers"])


def test_list_is_ordered_by_name(client: TestClient, auth_headers: dict) -> None:
    for name in ("z-provider", "a-provider", "m-provider"):
        client.post(
            "/api/v1/llm-providers",
            json={
                "name": name,
                "provider_type": "ollama",
                "default_model": "x",
            },
            headers=auth_headers,
        )
    resp = client.get("/api/v1/llm-providers", headers=auth_headers)
    names = [p["name"] for p in resp.json()["providers"]]
    assert names == sorted(names)

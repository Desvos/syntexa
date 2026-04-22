"""CRUD tests for /api/v1/agents."""
from __future__ import annotations

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from syntexa.core import crypto


@pytest.fixture(autouse=True)
def _isolated_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYNTEXA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    crypto.reset_cache_for_tests()


def _make_provider(
    client: TestClient,
    auth_headers: dict,
    name: str = "prov-a",
    provider_type: str = "ollama",
    default_model: str = "llama3.1",
) -> int:
    """Seed an LLMProvider and return its id. Ollama has no key requirement."""
    payload: dict = {
        "name": name,
        "provider_type": provider_type,
        "default_model": default_model,
    }
    if provider_type != "ollama":
        payload["api_key"] = "sk-test-abc-1234567890"
    resp = client.post("/api/v1/llm-providers", json=payload, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_create_agent_succeeds_and_lowercases_name(
    client: TestClient, auth_headers: dict
) -> None:
    provider_id = _make_provider(client, auth_headers)
    resp = client.post(
        "/api/v1/agents",
        json={
            "name": "Planner-One",
            "system_prompt": "You plan.",
            "provider_id": provider_id,
            "model": "llama3.1:8b",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "planner-one"
    assert data["system_prompt"] == "You plan."
    assert data["provider_id"] == provider_id
    assert data["model"] == "llama3.1:8b"
    assert data["is_active"] is True


def test_create_rejects_non_slug_name(client: TestClient, auth_headers: dict) -> None:
    provider_id = _make_provider(client, auth_headers)
    resp = client.post(
        "/api/v1/agents",
        json={
            "name": "not a slug!",
            "system_prompt": "x",
            "provider_id": provider_id,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422, resp.text


def test_create_rejects_unknown_provider_id(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.post(
        "/api/v1/agents",
        json={
            "name": "orphan",
            "system_prompt": "x",
            "provider_id": 99999,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422, resp.text
    assert "provider_id" in resp.text.lower() or "provider" in resp.text.lower()


def test_create_rejects_duplicate_name(
    client: TestClient, auth_headers: dict
) -> None:
    provider_id = _make_provider(client, auth_headers)
    payload = {
        "name": "dup",
        "system_prompt": "x",
        "provider_id": provider_id,
    }
    assert (
        client.post("/api/v1/agents", json=payload, headers=auth_headers).status_code
        == 201
    )
    resp = client.post("/api/v1/agents", json=payload, headers=auth_headers)
    assert resp.status_code == 409, resp.text


def test_create_without_model_stores_null_and_reads_back(
    client: TestClient, auth_headers: dict
) -> None:
    provider_id = _make_provider(client, auth_headers)
    resp = client.post(
        "/api/v1/agents",
        json={
            "name": "no-model",
            "system_prompt": "x",
            "provider_id": provider_id,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["model"] is None

    listing = client.get("/api/v1/agents", headers=auth_headers).json()
    row = next(a for a in listing["agents"] if a["name"] == "no-model")
    assert row["model"] is None


def test_update_patches_fields_without_touching_name(
    client: TestClient, auth_headers: dict
) -> None:
    provider_id = _make_provider(client, auth_headers)
    created = client.post(
        "/api/v1/agents",
        json={
            "name": "patch-me",
            "system_prompt": "old prompt",
            "provider_id": provider_id,
            "model": "llama3.1",
        },
        headers=auth_headers,
    ).json()

    resp = client.put(
        f"/api/v1/agents/{created['id']}",
        json={
            "system_prompt": "new prompt",
            "model": "llama3.1:70b",
            "is_active": False,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "patch-me"  # unchanged
    assert data["system_prompt"] == "new prompt"
    assert data["model"] == "llama3.1:70b"
    assert data["is_active"] is False


def test_update_404_on_missing(client: TestClient, auth_headers: dict) -> None:
    resp = client.put(
        "/api/v1/agents/9999",
        json={"system_prompt": "noop"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_update_unknown_provider_id_rejected(
    client: TestClient, auth_headers: dict
) -> None:
    provider_id = _make_provider(client, auth_headers)
    created = client.post(
        "/api/v1/agents",
        json={
            "name": "swap-provider",
            "system_prompt": "x",
            "provider_id": provider_id,
        },
        headers=auth_headers,
    ).json()

    resp = client.put(
        f"/api/v1/agents/{created['id']}",
        json={"provider_id": 9999},
        headers=auth_headers,
    )
    assert resp.status_code == 422, resp.text


def test_delete_returns_204_and_list_drops_row(
    client: TestClient, auth_headers: dict
) -> None:
    provider_id = _make_provider(client, auth_headers)
    created = client.post(
        "/api/v1/agents",
        json={
            "name": "gone",
            "system_prompt": "x",
            "provider_id": provider_id,
        },
        headers=auth_headers,
    ).json()

    resp = client.delete(f"/api/v1/agents/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204

    listing = client.get("/api/v1/agents", headers=auth_headers).json()
    assert all(a["id"] != created["id"] for a in listing["agents"])


def test_list_ordered_by_name(client: TestClient, auth_headers: dict) -> None:
    provider_id = _make_provider(client, auth_headers)
    for name in ("zeta", "alpha", "mu"):
        resp = client.post(
            "/api/v1/agents",
            json={
                "name": name,
                "system_prompt": "x",
                "provider_id": provider_id,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text

    resp = client.get("/api/v1/agents", headers=auth_headers)
    assert resp.status_code == 200
    names = [a["name"] for a in resp.json()["agents"]]
    assert names == sorted(names)

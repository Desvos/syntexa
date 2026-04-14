"""T039 — CRUD tests for /api/v1/roles."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from syntexa.api.main import create_app
from syntexa.config import get_settings
from syntexa.models import (
    AgentRole,
    SwarmComposition,
    create_all,
    session_scope,
)


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    """Fresh FastAPI app + SQLite DB per test.

    We point `Settings.database_url` at a temp file, then the app's
    lifespan handler calls init_engine() against that URL on __enter__.
    Tables are created AFTER TestClient enters, so they hit the same
    engine the app uses."""
    db_url = f"sqlite:///{tmp_path / 'api.db'}"
    monkeypatch.setenv("SYNTEXA_DATABASE_URL", db_url)
    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as c:
        create_all()
        yield c
    get_settings.cache_clear()


def _seed_default_role(name: str = "planner") -> AgentRole:
    with session_scope() as s:
        role = AgentRole(
            name=name,
            system_prompt=f"Default {name} prompt.",
            is_default=True,
        )
        role.set_handoff_targets(["coder"])
        s.add(role)
        s.flush()
        s.refresh(role)
        # Detach so the caller can read attrs outside the session.
        s.expunge(role)
    return role


def test_list_roles_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/roles")
    assert resp.status_code == 200
    assert resp.json() == {"roles": []}


def test_create_role_roundtrip(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/roles",
        json={
            "name": "security-auditor",
            "system_prompt": "You audit the diff for security issues.",
            "handoff_targets": ["coder", "reviewer"],
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "security-auditor"
    assert data["handoff_targets"] == ["coder", "reviewer"]
    assert data["is_default"] is False

    listing = client.get("/api/v1/roles").json()
    assert len(listing["roles"]) == 1
    assert listing["roles"][0]["name"] == "security-auditor"


def test_create_role_rejects_duplicate_name(client: TestClient) -> None:
    payload = {"name": "reviewer", "system_prompt": "x", "handoff_targets": []}
    assert client.post("/api/v1/roles", json=payload).status_code == 201
    resp = client.post("/api/v1/roles", json=payload)
    assert resp.status_code == 409


def test_create_role_validates_name(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/roles",
        json={"name": "bad name!", "system_prompt": "x", "handoff_targets": []},
    )
    assert resp.status_code == 422


def test_create_role_rejects_duplicate_handoffs(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/roles",
        json={"name": "x", "system_prompt": "y", "handoff_targets": ["a", "a"]},
    )
    assert resp.status_code == 422


def test_update_role_partial(client: TestClient) -> None:
    created = client.post(
        "/api/v1/roles",
        json={"name": "custom", "system_prompt": "old", "handoff_targets": []},
    ).json()
    role_id = created["id"]

    resp = client.put(
        f"/api/v1/roles/{role_id}",
        json={"system_prompt": "new prompt"},
    )
    assert resp.status_code == 200
    assert resp.json()["system_prompt"] == "new prompt"
    # handoff_targets unchanged when omitted.
    assert resp.json()["handoff_targets"] == []


def test_update_role_replaces_handoffs(client: TestClient) -> None:
    created = client.post(
        "/api/v1/roles",
        json={"name": "custom", "system_prompt": "x", "handoff_targets": ["a"]},
    ).json()
    resp = client.put(
        f"/api/v1/roles/{created['id']}",
        json={"handoff_targets": ["b", "c"]},
    )
    assert resp.status_code == 200
    assert resp.json()["handoff_targets"] == ["b", "c"]


def test_update_missing_role_returns_404(client: TestClient) -> None:
    resp = client.put("/api/v1/roles/99999", json={"system_prompt": "x"})
    assert resp.status_code == 404


def test_delete_custom_role(client: TestClient) -> None:
    created = client.post(
        "/api/v1/roles",
        json={"name": "custom", "system_prompt": "x", "handoff_targets": []},
    ).json()
    resp = client.delete(f"/api/v1/roles/{created['id']}")
    assert resp.status_code == 204
    assert client.get("/api/v1/roles").json() == {"roles": []}


def test_delete_default_role_blocked(client: TestClient) -> None:
    role = _seed_default_role("planner")
    resp = client.delete(f"/api/v1/roles/{role.id}")
    assert resp.status_code == 409
    assert "default" in resp.json()["detail"].lower()


def test_delete_role_in_use_blocked(client: TestClient) -> None:
    created = client.post(
        "/api/v1/roles",
        json={"name": "custom", "system_prompt": "x", "handoff_targets": []},
    ).json()

    # Hand-stitch a composition that references the custom role.
    with session_scope() as s:
        comp = SwarmComposition(task_type="feature", max_rounds=60)
        comp.set_roles(["custom", "reviewer"])
        s.add(comp)

    resp = client.delete(f"/api/v1/roles/{created['id']}")
    assert resp.status_code == 409
    assert "feature" in resp.json()["detail"]


def test_delete_missing_role_returns_404(client: TestClient) -> None:
    resp = client.delete("/api/v1/roles/99999")
    assert resp.status_code == 404


def test_health_endpoint(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": "0.1.0"}

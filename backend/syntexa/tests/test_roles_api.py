"""T039 — CRUD tests for /api/v1/roles."""
from __future__ import annotations

from fastapi.testclient import TestClient

from syntexa.models import (
    AgentRole,
    SwarmComposition,
    session_scope,
)


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


def test_list_roles_empty(client: TestClient, auth_headers: dict) -> None:
    resp = client.get("/api/v1/roles", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"roles": []}


def test_create_role_roundtrip(client: TestClient, auth_headers: dict) -> None:
    resp = client.post(
        "/api/v1/roles",
        json={
            "name": "security-auditor",
            "system_prompt": "You audit the diff for security issues.",
            "handoff_targets": ["coder", "reviewer"],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "security-auditor"
    assert data["handoff_targets"] == ["coder", "reviewer"]
    assert data["is_default"] is False

    listing = client.get("/api/v1/roles", headers=auth_headers).json()
    assert len(listing["roles"]) == 1
    assert listing["roles"][0]["name"] == "security-auditor"


def test_create_role_rejects_duplicate_name(client: TestClient, auth_headers: dict) -> None:
    payload = {"name": "reviewer", "system_prompt": "x", "handoff_targets": []}
    assert client.post("/api/v1/roles", json=payload, headers=auth_headers).status_code == 201
    resp = client.post("/api/v1/roles", json=payload, headers=auth_headers)
    assert resp.status_code == 409


def test_create_role_validates_name(client: TestClient, auth_headers: dict) -> None:
    resp = client.post(
        "/api/v1/roles",
        json={"name": "bad name!", "system_prompt": "x", "handoff_targets": []},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_role_rejects_duplicate_handoffs(client: TestClient, auth_headers: dict) -> None:
    resp = client.post(
        "/api/v1/roles",
        json={"name": "x", "system_prompt": "y", "handoff_targets": ["a", "a"]},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_update_role_partial(client: TestClient, auth_headers: dict) -> None:
    created = client.post(
        "/api/v1/roles",
        json={"name": "custom", "system_prompt": "old", "handoff_targets": []},
        headers=auth_headers,
    ).json()
    role_id = created["id"]

    resp = client.put(
        f"/api/v1/roles/{role_id}",
        json={"system_prompt": "new prompt"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["system_prompt"] == "new prompt"
    # handoff_targets unchanged when omitted.
    assert resp.json()["handoff_targets"] == []


def test_update_role_replaces_handoffs(client: TestClient, auth_headers: dict) -> None:
    created = client.post(
        "/api/v1/roles",
        json={"name": "custom", "system_prompt": "x", "handoff_targets": ["a"]},
        headers=auth_headers,
    ).json()
    resp = client.put(
        f"/api/v1/roles/{created['id']}",
        json={"handoff_targets": ["b", "c"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["handoff_targets"] == ["b", "c"]


def test_update_missing_role_returns_404(client: TestClient, auth_headers: dict) -> None:
    resp = client.put("/api/v1/roles/99999", json={"system_prompt": "x"}, headers=auth_headers)
    assert resp.status_code == 404


def test_delete_custom_role(client: TestClient, auth_headers: dict) -> None:
    created = client.post(
        "/api/v1/roles",
        json={"name": "custom", "system_prompt": "x", "handoff_targets": []},
        headers=auth_headers,
    ).json()
    resp = client.delete(f"/api/v1/roles/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get("/api/v1/roles", headers=auth_headers).json() == {"roles": []}


def test_delete_default_role_blocked(client: TestClient, auth_headers: dict) -> None:
    role = _seed_default_role("planner")
    resp = client.delete(f"/api/v1/roles/{role.id}", headers=auth_headers)
    assert resp.status_code == 409
    assert "default" in resp.json()["detail"].lower()


def test_delete_role_in_use_blocked(client: TestClient, auth_headers: dict) -> None:
    created = client.post(
        "/api/v1/roles",
        json={"name": "custom", "system_prompt": "x", "handoff_targets": []},
        headers=auth_headers,
    ).json()

    # Hand-stitch a composition that references the custom role.
    with session_scope() as s:
        comp = SwarmComposition(task_type="feature", max_rounds=60)
        comp.set_roles(["custom", "reviewer"])
        s.add(comp)

    resp = client.delete(f"/api/v1/roles/{created['id']}", headers=auth_headers)
    assert resp.status_code == 409
    assert "feature" in resp.json()["detail"]


def test_delete_missing_role_returns_404(client: TestClient, auth_headers: dict) -> None:
    resp = client.delete("/api/v1/roles/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_health_endpoint(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": "0.1.0"}

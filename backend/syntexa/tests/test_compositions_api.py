"""T050 — CRUD tests for /api/v1/compositions."""
from __future__ import annotations

from fastapi.testclient import TestClient

from syntexa.models import AgentRole, session_scope


def _seed_roles(names: tuple[str, ...]) -> None:
    with session_scope() as s:
        for name in names:
            role = AgentRole(
                name=name, system_prompt=f"{name} prompt", is_default=True
            )
            role.set_handoff_targets([])
            s.add(role)


def test_list_compositions_empty(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    resp = client.get("/api/v1/compositions", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"compositions": []}


def test_create_composition_roundtrip(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    resp = client.post(
        "/api/v1/compositions",
        json={
            "task_type": "feature",
            "roles": ["planner", "coder", "reviewer"],
            "max_rounds": 50,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["task_type"] == "feature"
    assert data["roles"] == ["planner", "coder", "reviewer"]
    assert data["max_rounds"] == 50

    listing = client.get("/api/v1/compositions", headers=auth_headers).json()
    assert len(listing["compositions"]) == 1


def test_create_composition_defaults_max_rounds(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    resp = client.post(
        "/api/v1/compositions",
        json={"task_type": "chore", "roles": ["coder"]},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["max_rounds"] == 60


def test_create_composition_rejects_duplicate_task_type(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    payload = {"task_type": "fix", "roles": ["coder"]}
    assert client.post("/api/v1/compositions", json=payload, headers=auth_headers).status_code == 201
    resp = client.post("/api/v1/compositions", json=payload, headers=auth_headers)
    assert resp.status_code == 409


def test_create_composition_rejects_unknown_task_type(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    resp = client.post(
        "/api/v1/compositions",
        json={"task_type": "nonsense", "roles": ["coder"]},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_composition_rejects_unknown_role(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    resp = client.post(
        "/api/v1/compositions",
        json={"task_type": "feature", "roles": ["planner", "ghost"]},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert "ghost" in resp.json()["detail"]


def test_create_composition_rejects_empty_roles(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    resp = client.post(
        "/api/v1/compositions",
        json={"task_type": "feature", "roles": []},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_composition_accepts_duplicate_roles_for_parallel_work(
    client: TestClient, auth_headers: dict
) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    # DEFAULT_COMPOSITIONS has refactor = (planner, coder, coder, tester, reviewer)
    resp = client.post(
        "/api/v1/compositions",
        json={
            "task_type": "refactor",
            "roles": ["planner", "coder", "coder", "tester", "reviewer"],
            "max_rounds": 80,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["roles"] == ["planner", "coder", "coder", "tester", "reviewer"]


def test_update_composition_replaces_roles(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    created = client.post(
        "/api/v1/compositions",
        json={"task_type": "feature", "roles": ["planner", "coder"]},
        headers=auth_headers,
    ).json()
    resp = client.put(
        f"/api/v1/compositions/{created['id']}",
        json={"roles": ["coder", "reviewer"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["roles"] == ["coder", "reviewer"]
    # max_rounds untouched when omitted.
    assert resp.json()["max_rounds"] == created["max_rounds"]


def test_update_composition_updates_max_rounds(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    created = client.post(
        "/api/v1/compositions",
        json={"task_type": "security", "roles": ["planner", "coder"]},
        headers=auth_headers,
    ).json()
    resp = client.put(
        f"/api/v1/compositions/{created['id']}",
        json={"max_rounds": 20},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["max_rounds"] == 20


def test_update_composition_rejects_unknown_role(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    created = client.post(
        "/api/v1/compositions",
        json={"task_type": "feature", "roles": ["planner"]},
        headers=auth_headers,
    ).json()
    resp = client.put(
        f"/api/v1/compositions/{created['id']}",
        json={"roles": ["planner", "ghost"]},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_update_missing_composition_returns_404(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    resp = client.put("/api/v1/compositions/99999", json={"max_rounds": 10}, headers=auth_headers)
    assert resp.status_code == 404


def test_delete_composition(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    created = client.post(
        "/api/v1/compositions",
        json={"task_type": "feature", "roles": ["coder"]},
        headers=auth_headers,
    ).json()
    resp = client.delete(f"/api/v1/compositions/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get("/api/v1/compositions", headers=auth_headers).json() == {"compositions": []}


def test_delete_missing_composition_returns_404(client: TestClient, auth_headers: dict) -> None:
    _seed_roles(("planner", "coder", "tester", "reviewer"))
    resp = client.delete("/api/v1/compositions/99999", headers=auth_headers)
    assert resp.status_code == 404

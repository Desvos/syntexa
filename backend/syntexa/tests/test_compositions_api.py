"""T050 — CRUD tests for /api/v1/compositions."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from syntexa.api.main import create_app
from syntexa.config import get_settings
from syntexa.models import AgentRole, create_all, session_scope


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    db_url = f"sqlite:///{tmp_path / 'api.db'}"
    monkeypatch.setenv("SYNTEXA_DATABASE_URL", db_url)
    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as c:
        create_all()
        _seed_roles(("planner", "coder", "tester", "reviewer"))
        yield c
    get_settings.cache_clear()


def _seed_roles(names: tuple[str, ...]) -> None:
    with session_scope() as s:
        for name in names:
            role = AgentRole(
                name=name, system_prompt=f"{name} prompt", is_default=True
            )
            role.set_handoff_targets([])
            s.add(role)


def test_list_compositions_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/compositions")
    assert resp.status_code == 200
    assert resp.json() == {"compositions": []}


def test_create_composition_roundtrip(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/compositions",
        json={
            "task_type": "feature",
            "roles": ["planner", "coder", "reviewer"],
            "max_rounds": 50,
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["task_type"] == "feature"
    assert data["roles"] == ["planner", "coder", "reviewer"]
    assert data["max_rounds"] == 50

    listing = client.get("/api/v1/compositions").json()
    assert len(listing["compositions"]) == 1


def test_create_composition_defaults_max_rounds(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/compositions",
        json={"task_type": "chore", "roles": ["coder"]},
    )
    assert resp.status_code == 201
    assert resp.json()["max_rounds"] == 60


def test_create_composition_rejects_duplicate_task_type(client: TestClient) -> None:
    payload = {"task_type": "fix", "roles": ["coder"]}
    assert client.post("/api/v1/compositions", json=payload).status_code == 201
    resp = client.post("/api/v1/compositions", json=payload)
    assert resp.status_code == 409


def test_create_composition_rejects_unknown_task_type(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/compositions",
        json={"task_type": "nonsense", "roles": ["coder"]},
    )
    assert resp.status_code == 422


def test_create_composition_rejects_unknown_role(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/compositions",
        json={"task_type": "feature", "roles": ["planner", "ghost"]},
    )
    assert resp.status_code == 422
    assert "ghost" in resp.json()["detail"]


def test_create_composition_rejects_empty_roles(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/compositions",
        json={"task_type": "feature", "roles": []},
    )
    assert resp.status_code == 422


def test_create_composition_accepts_duplicate_roles_for_parallel_work(
    client: TestClient,
) -> None:
    # DEFAULT_COMPOSITIONS has refactor = (planner, coder, coder, tester, reviewer)
    resp = client.post(
        "/api/v1/compositions",
        json={
            "task_type": "refactor",
            "roles": ["planner", "coder", "coder", "tester", "reviewer"],
            "max_rounds": 80,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["roles"] == ["planner", "coder", "coder", "tester", "reviewer"]


def test_update_composition_replaces_roles(client: TestClient) -> None:
    created = client.post(
        "/api/v1/compositions",
        json={"task_type": "feature", "roles": ["planner", "coder"]},
    ).json()
    resp = client.put(
        f"/api/v1/compositions/{created['id']}",
        json={"roles": ["coder", "reviewer"]},
    )
    assert resp.status_code == 200
    assert resp.json()["roles"] == ["coder", "reviewer"]
    # max_rounds untouched when omitted.
    assert resp.json()["max_rounds"] == created["max_rounds"]


def test_update_composition_updates_max_rounds(client: TestClient) -> None:
    created = client.post(
        "/api/v1/compositions",
        json={"task_type": "security", "roles": ["planner", "coder"]},
    ).json()
    resp = client.put(
        f"/api/v1/compositions/{created['id']}",
        json={"max_rounds": 20},
    )
    assert resp.status_code == 200
    assert resp.json()["max_rounds"] == 20


def test_update_composition_rejects_unknown_role(client: TestClient) -> None:
    created = client.post(
        "/api/v1/compositions",
        json={"task_type": "feature", "roles": ["planner"]},
    ).json()
    resp = client.put(
        f"/api/v1/compositions/{created['id']}",
        json={"roles": ["planner", "ghost"]},
    )
    assert resp.status_code == 422


def test_update_missing_composition_returns_404(client: TestClient) -> None:
    resp = client.put("/api/v1/compositions/99999", json={"max_rounds": 10})
    assert resp.status_code == 404


def test_delete_composition(client: TestClient) -> None:
    created = client.post(
        "/api/v1/compositions",
        json={"task_type": "feature", "roles": ["coder"]},
    ).json()
    resp = client.delete(f"/api/v1/compositions/{created['id']}")
    assert resp.status_code == 204
    assert client.get("/api/v1/compositions").json() == {"compositions": []}


def test_delete_missing_composition_returns_404(client: TestClient) -> None:
    resp = client.delete("/api/v1/compositions/99999")
    assert resp.status_code == 404

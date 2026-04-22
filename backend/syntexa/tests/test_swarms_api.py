"""CRUD tests for /api/v1/swarms (first-class Swarm entity, Phase 4)."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


# --- helpers -------------------------------------------------------------


def _abs_path(p: Path) -> str:
    return p.resolve().as_posix()


def _make_provider(client: TestClient, auth_headers: dict, name: str = "p1") -> int:
    resp = client.post(
        "/api/v1/llm-providers",
        json={
            "name": name,
            "provider_type": "anthropic",
            "api_key": "sk-ant-test-xxxxxxxx",
            "default_model": "claude-sonnet-4.5",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _make_agent(
    client: TestClient,
    auth_headers: dict,
    provider_id: int,
    name: str,
) -> int:
    resp = client.post(
        "/api/v1/agents",
        json={
            "name": name,
            "system_prompt": f"You are {name}.",
            "provider_id": provider_id,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _make_repository(
    client: TestClient,
    auth_headers: dict,
    tmp_path: Path,
    name: str = "repo1",
) -> int:
    sub = tmp_path / name
    sub.mkdir(exist_ok=True)
    resp = client.post(
        "/api/v1/repositories",
        json={"name": name, "path": _abs_path(sub)},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _seed_minimum(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> tuple[int, list[int]]:
    """Create one repo + two agents. Returns (repo_id, [agent_ids])."""
    provider_id = _make_provider(client, auth_headers)
    repo_id = _make_repository(client, auth_headers, tmp_path)
    a1 = _make_agent(client, auth_headers, provider_id, "alice")
    a2 = _make_agent(client, auth_headers, provider_id, "bob")
    return repo_id, [a1, a2]


# --- create --------------------------------------------------------------


def test_create_happy_path(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id, agent_ids = _seed_minimum(client, auth_headers, tmp_path)

    resp = client.post(
        "/api/v1/swarms",
        json={
            "name": "MySwarm",
            "repository_id": repo_id,
            "task_description": "Refactor the auth module",
            "orchestrator_strategy": "auto",
            "max_rounds": 20,
            "agent_ids": agent_ids,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "myswarm"
    assert data["repository_id"] == repo_id
    assert data["task_description"] == "Refactor the auth module"
    assert data["orchestrator_strategy"] == "auto"
    assert data["max_rounds"] == 20
    assert data["status"] == "idle"
    assert data["is_active"] is True
    assert data["manual_agent_order"] is None
    assert [a["id"] for a in data["agents"]] == agent_ids
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_rejects_duplicate_name(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id, agent_ids = _seed_minimum(client, auth_headers, tmp_path)
    payload = {
        "name": "dup",
        "repository_id": repo_id,
        "agent_ids": agent_ids,
    }
    assert (
        client.post("/api/v1/swarms", json=payload, headers=auth_headers).status_code
        == 201
    )
    resp = client.post("/api/v1/swarms", json=payload, headers=auth_headers)
    assert resp.status_code == 409


def test_create_rejects_unknown_repository_id(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    provider_id = _make_provider(client, auth_headers)
    agent_id = _make_agent(client, auth_headers, provider_id, "solo")

    resp = client.post(
        "/api/v1/swarms",
        json={
            "name": "no-repo",
            "repository_id": 99999,
            "agent_ids": [agent_id],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert "repository_id" in resp.text.lower()


def test_create_rejects_unknown_agent_id(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id = _make_repository(client, auth_headers, tmp_path)
    resp = client.post(
        "/api/v1/swarms",
        json={
            "name": "bad-agents",
            "repository_id": repo_id,
            "agent_ids": [4242],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert "agent_id" in resp.text.lower()


def test_create_rejects_empty_agent_ids(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id = _make_repository(client, auth_headers, tmp_path)
    resp = client.post(
        "/api/v1/swarms",
        json={
            "name": "empty",
            "repository_id": repo_id,
            "agent_ids": [],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_rejects_invalid_strategy(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id, agent_ids = _seed_minimum(client, auth_headers, tmp_path)
    resp = client.post(
        "/api/v1/swarms",
        json={
            "name": "bad-strategy",
            "repository_id": repo_id,
            "orchestrator_strategy": "weird-mode",
            "agent_ids": agent_ids,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_rejects_invalid_status(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id, agent_ids = _seed_minimum(client, auth_headers, tmp_path)
    resp = client.post(
        "/api/v1/swarms",
        json={
            "name": "bad-status",
            "repository_id": repo_id,
            "status": "on-fire",
            "agent_ids": agent_ids,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_rejects_manual_order_without_sequential(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id, agent_ids = _seed_minimum(client, auth_headers, tmp_path)
    resp = client.post(
        "/api/v1/swarms",
        json={
            "name": "bad-order-strat",
            "repository_id": repo_id,
            "orchestrator_strategy": "parallel",
            "manual_agent_order": [agent_ids[0]],
            "agent_ids": agent_ids,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert "sequential" in resp.text.lower()


def test_create_rejects_manual_order_with_foreign_agent(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id, agent_ids = _seed_minimum(client, auth_headers, tmp_path)
    resp = client.post(
        "/api/v1/swarms",
        json={
            "name": "bad-order-mem",
            "repository_id": repo_id,
            "orchestrator_strategy": "sequential",
            "manual_agent_order": [agent_ids[0], 98765],
            "agent_ids": agent_ids,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_accepts_sequential_with_manual_order(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id, agent_ids = _seed_minimum(client, auth_headers, tmp_path)
    resp = client.post(
        "/api/v1/swarms",
        json={
            "name": "seq",
            "repository_id": repo_id,
            "orchestrator_strategy": "sequential",
            "manual_agent_order": list(reversed(agent_ids)),
            "agent_ids": agent_ids,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["manual_agent_order"] == list(reversed(agent_ids))


def test_create_rejects_non_slug_name(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id, agent_ids = _seed_minimum(client, auth_headers, tmp_path)
    resp = client.post(
        "/api/v1/swarms",
        json={
            "name": "bad name!",
            "repository_id": repo_id,
            "agent_ids": agent_ids,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


# --- list ----------------------------------------------------------------


def test_list_filters_by_repository_id(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    provider_id = _make_provider(client, auth_headers)
    repo_a = _make_repository(client, auth_headers, tmp_path, "repo-a")
    repo_b = _make_repository(client, auth_headers, tmp_path, "repo-b")
    a1 = _make_agent(client, auth_headers, provider_id, "a1")

    client.post(
        "/api/v1/swarms",
        json={"name": "in-a", "repository_id": repo_a, "agent_ids": [a1]},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/swarms",
        json={"name": "in-b", "repository_id": repo_b, "agent_ids": [a1]},
        headers=auth_headers,
    )

    resp = client.get(
        f"/api/v1/swarms?repository_id={repo_a}", headers=auth_headers
    )
    assert resp.status_code == 200
    swarms = resp.json()["swarms"]
    assert len(swarms) == 1
    assert swarms[0]["name"] == "in-a"


def test_list_filters_by_status(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id, agent_ids = _seed_minimum(client, auth_headers, tmp_path)
    client.post(
        "/api/v1/swarms",
        json={
            "name": "idle-one",
            "repository_id": repo_id,
            "agent_ids": agent_ids,
        },
        headers=auth_headers,
    )
    client.post(
        "/api/v1/swarms",
        json={
            "name": "running-one",
            "repository_id": repo_id,
            "status": "running",
            "agent_ids": agent_ids,
        },
        headers=auth_headers,
    )

    resp = client.get("/api/v1/swarms?status=running", headers=auth_headers)
    assert resp.status_code == 200
    names = [s["name"] for s in resp.json()["swarms"]]
    assert names == ["running-one"]


# --- patch ---------------------------------------------------------------


def test_patch_replaces_agent_ids(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    provider_id = _make_provider(client, auth_headers)
    repo_id = _make_repository(client, auth_headers, tmp_path)
    a1 = _make_agent(client, auth_headers, provider_id, "a1")
    a2 = _make_agent(client, auth_headers, provider_id, "a2")
    a3 = _make_agent(client, auth_headers, provider_id, "a3")

    created = client.post(
        "/api/v1/swarms",
        json={
            "name": "patchable",
            "repository_id": repo_id,
            "agent_ids": [a1, a2],
        },
        headers=auth_headers,
    ).json()

    resp = client.patch(
        f"/api/v1/swarms/{created['id']}",
        json={"agent_ids": [a3, a1]},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert [a["id"] for a in resp.json()["agents"]] == [a3, a1]


def test_patch_404_on_missing_id(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.patch(
        "/api/v1/swarms/99999",
        json={"task_description": "nope"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_patch_rejects_manual_order_when_strategy_not_sequential(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id, agent_ids = _seed_minimum(client, auth_headers, tmp_path)
    created = client.post(
        "/api/v1/swarms",
        json={
            "name": "keep-auto",
            "repository_id": repo_id,
            "agent_ids": agent_ids,
        },
        headers=auth_headers,
    ).json()

    resp = client.patch(
        f"/api/v1/swarms/{created['id']}",
        json={"manual_agent_order": [agent_ids[0]]},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# --- get -----------------------------------------------------------------


def test_get_404_on_missing_id(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.get("/api/v1/swarms/99999", headers=auth_headers)
    assert resp.status_code == 404


# --- delete --------------------------------------------------------------


def test_delete_cascades_join_rows_but_preserves_agents_and_repo(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    repo_id, agent_ids = _seed_minimum(client, auth_headers, tmp_path)
    created = client.post(
        "/api/v1/swarms",
        json={
            "name": "ephemeral",
            "repository_id": repo_id,
            "agent_ids": agent_ids,
        },
        headers=auth_headers,
    ).json()

    resp = client.delete(
        f"/api/v1/swarms/{created['id']}", headers=auth_headers
    )
    assert resp.status_code == 204

    # Swarm gone
    assert (
        client.get(
            f"/api/v1/swarms/{created['id']}", headers=auth_headers
        ).status_code
        == 404
    )

    # Agents and repository still present
    agents = client.get("/api/v1/agents", headers=auth_headers).json()["agents"]
    assert {a["id"] for a in agents} >= set(agent_ids)

    repos = client.get(
        "/api/v1/repositories", headers=auth_headers
    ).json()["repositories"]
    assert any(r["id"] == repo_id for r in repos)

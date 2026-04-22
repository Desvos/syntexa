"""HTTP tests for POST /api/v1/swarms/{id}/run.

We mock ``syntexa.orchestrator.run_swarm`` at the route module's
namespace so the test just verifies wiring: path, status codes, error
mapping. The executor itself is covered by test_orchestrator_executor.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from syntexa.orchestrator.executor import (
    OrchestratorResult,
    SwarmAlreadyRunningError,
    SwarmNotFoundError,
)


# --- helpers mirrored from test_swarms_api.py ---------------------------


def _abs_path(p: Path) -> str:
    return p.resolve().as_posix()


def _make_provider(client: TestClient, auth_headers: dict) -> int:
    resp = client.post(
        "/api/v1/llm-providers",
        json={
            "name": "p1",
            "provider_type": "anthropic",
            "api_key": "sk-ant-test-xxxxxxxx",
            "default_model": "claude-sonnet-4.5",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _make_agent(
    client: TestClient, auth_headers: dict, provider_id: int, name: str
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


def _make_repo(client: TestClient, auth_headers: dict, tmp_path: Path) -> int:
    sub = tmp_path / "r1"
    sub.mkdir(exist_ok=True)
    resp = client.post(
        "/api/v1/repositories",
        json={"name": "r1", "path": _abs_path(sub)},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _seed_swarm(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> int:
    provider_id = _make_provider(client, auth_headers)
    repo_id = _make_repo(client, auth_headers, tmp_path)
    a1 = _make_agent(client, auth_headers, provider_id, "alice")
    a2 = _make_agent(client, auth_headers, provider_id, "bob")
    resp = client.post(
        "/api/v1/swarms",
        json={
            "name": "myswarm",
            "repository_id": repo_id,
            "task_description": "Refactor auth",
            "orchestrator_strategy": "parallel",
            "agent_ids": [a1, a2],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# --- happy path ---------------------------------------------------------


def test_run_returns_orchestrator_result(
    client: TestClient,
    auth_headers: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    swarm_id = _seed_swarm(client, auth_headers, tmp_path)

    captured: dict = {}

    def fake_impl(
        sid: int,
        task_override: str | None = None,
        *,
        meta_provider_id: int | None = None,
        session=None,
    ) -> OrchestratorResult:
        captured["swarm_id"] = sid
        captured["task_override"] = task_override
        captured["meta_provider_id"] = meta_provider_id
        return OrchestratorResult(
            swarm_id=sid,
            strategy_used="parallel",
            order=None,
            agent_outputs={1: "hi", 2: "yo"},
            success=True,
            error=None,
        )

    monkeypatch.setattr(
        "syntexa.api.routes.swarms.run_swarm_impl", fake_impl
    )

    resp = client.post(
        f"/api/v1/swarms/{swarm_id}/run",
        json={"task_override": "Do the thing"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["swarm_id"] == swarm_id
    assert data["strategy_used"] == "parallel"
    assert data["order"] is None
    # dict keys are stringified in JSON — that's what the schema specifies.
    assert data["agent_outputs"] == {"1": "hi", "2": "yo"}
    assert data["success"] is True
    assert data["error"] is None
    # Payload flowed through correctly.
    assert captured["swarm_id"] == swarm_id
    assert captured["task_override"] == "Do the thing"
    assert captured["meta_provider_id"] is None


def test_run_accepts_empty_body(
    client: TestClient,
    auth_headers: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /run with no body should still fire (all fields optional)."""
    swarm_id = _seed_swarm(client, auth_headers, tmp_path)

    def fake_impl(sid, task_override=None, *, meta_provider_id=None, session=None):
        return OrchestratorResult(
            swarm_id=sid,
            strategy_used="parallel",
            order=None,
            agent_outputs={},
            success=True,
            error=None,
        )

    monkeypatch.setattr(
        "syntexa.api.routes.swarms.run_swarm_impl", fake_impl
    )

    resp = client.post(
        f"/api/v1/swarms/{swarm_id}/run", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text


def test_run_forwards_meta_provider_id(
    client: TestClient,
    auth_headers: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    swarm_id = _seed_swarm(client, auth_headers, tmp_path)

    captured: dict = {}

    def fake_impl(sid, task_override=None, *, meta_provider_id=None, session=None):
        captured["meta_provider_id"] = meta_provider_id
        return OrchestratorResult(
            swarm_id=sid,
            strategy_used="parallel",
            order=None,
            agent_outputs={},
            success=True,
            error=None,
        )

    monkeypatch.setattr(
        "syntexa.api.routes.swarms.run_swarm_impl", fake_impl
    )

    resp = client.post(
        f"/api/v1/swarms/{swarm_id}/run",
        json={"meta_provider_id": 7},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert captured["meta_provider_id"] == 7


# --- error paths --------------------------------------------------------


def test_run_404_when_swarm_missing(
    client: TestClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_impl(*args, **kwargs):
        raise SwarmNotFoundError("Swarm id=99999 not found")

    monkeypatch.setattr(
        "syntexa.api.routes.swarms.run_swarm_impl", fake_impl
    )

    resp = client.post("/api/v1/swarms/99999/run", headers=auth_headers)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_run_409_when_already_running(
    client: TestClient,
    auth_headers: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    swarm_id = _seed_swarm(client, auth_headers, tmp_path)

    def fake_impl(*args, **kwargs):
        raise SwarmAlreadyRunningError(
            f"Swarm id={swarm_id} is already running"
        )

    monkeypatch.setattr(
        "syntexa.api.routes.swarms.run_swarm_impl", fake_impl
    )

    resp = client.post(
        f"/api/v1/swarms/{swarm_id}/run", headers=auth_headers
    )
    assert resp.status_code == 409
    assert "already running" in resp.json()["detail"].lower()


def test_run_surfaces_executor_failure_as_success_false(
    client: TestClient,
    auth_headers: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Executor errors that aren't 404/409 come back as success=False,
    NOT an HTTP 500 — the request itself succeeded; the run didn't."""
    swarm_id = _seed_swarm(client, auth_headers, tmp_path)

    def fake_impl(sid, task_override=None, *, meta_provider_id=None, session=None):
        return OrchestratorResult(
            swarm_id=sid,
            strategy_used="parallel",
            order=None,
            agent_outputs={},
            success=False,
            error="provider blew up",
        )

    monkeypatch.setattr(
        "syntexa.api.routes.swarms.run_swarm_impl", fake_impl
    )

    resp = client.post(
        f"/api/v1/swarms/{swarm_id}/run", headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["error"] == "provider blew up"


def test_run_requires_auth(client: TestClient, tmp_path: Path) -> None:
    """Unauth'd requests get 401 — auth middleware applies to /swarms."""
    resp = client.post("/api/v1/swarms/1/run")
    assert resp.status_code == 401

"""Tests for settings API endpoints (T064)."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from syntexa.api.main import create_app
from syntexa.config import get_settings
from syntexa.models import (
    SwarmInstance,
    SystemSetting,
    create_all,
    session_scope,
)


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    """Fresh FastAPI app + SQLite DB per test."""
    db_url = f"sqlite:///{tmp_path / 'api.db'}"
    monkeypatch.setenv("SYNTEXA_DATABASE_URL", db_url)
    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as c:
        create_all()
        yield c
    get_settings.cache_clear()


class TestSettingsEndpoints:
    """Tests for GET /api/v1/settings and PATCH /api/v1/settings."""

    def test_get_settings_returns_defaults(self, client: TestClient) -> None:
        """GET /settings returns default values on first call."""
        response = client.get("/api/v1/settings")
        assert response.status_code == 200

        data = response.json()
        assert "poll_interval" in data
        assert "max_concurrent" in data
        assert "log_retention_days" in data
        assert "agent_trigger_tag" in data
        assert "base_branch" in data
        assert "repo_path" in data

        # Default values
        assert data["poll_interval"] == 300
        assert data["max_concurrent"] == 3
        assert data["log_retention_days"] == 30
        assert data["agent_trigger_tag"] == "agent-swarm"
        assert data["base_branch"] == "main"

    def test_patch_settings_updates_values(self, client: TestClient) -> None:
        """PATCH /settings updates runtime-tunable settings."""
        response = client.patch(
            "/api/v1/settings",
            json={"poll_interval": 120, "max_concurrent": 5},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["poll_interval"] == 120
        assert data["max_concurrent"] == 5

    def test_patch_settings_validates_values(self, client: TestClient) -> None:
        """PATCH /settings rejects invalid values."""
        # poll_interval too low
        response = client.patch(
            "/api/v1/settings",
            json={"poll_interval": 5},
        )
        assert response.status_code == 422

        # max_concurrent too low
        response = client.patch(
            "/api/v1/settings",
            json={"max_concurrent": 0},
        )
        assert response.status_code == 422

        # log_retention_days too low
        response = client.patch(
            "/api/v1/settings",
            json={"log_retention_days": 0},
        )
        assert response.status_code == 422

    def test_patch_settings_with_invalid_field_excluded(self, client: TestClient) -> None:
        """PATCH /settings ignores unknown fields (not in schema)."""
        # repo_path is not in the update schema, so it's ignored
        response = client.patch(
            "/api/v1/settings",
            json={"repo_path": "/some/path"},
        )
        # Results in empty update, hence "No settings provided"
        assert response.status_code == 400
        assert "No settings provided" in response.json()["detail"]

    def test_patch_settings_requires_at_least_one_field(self, client: TestClient) -> None:
        """PATCH /settings requires at least one field to update."""
        response = client.patch("/api/v1/settings", json={})
        assert response.status_code == 400
        assert "No settings provided" in response.json()["detail"]

    def test_settings_persisted_to_database(self, client: TestClient) -> None:
        """Settings updates are stored in the database."""
        client.patch(
            "/api/v1/settings",
            json={"poll_interval": 180, "max_concurrent": 2},
        )

        # Check database
        with session_scope() as session:
            poll_setting = session.get(SystemSetting, "poll_interval")
            assert poll_setting is not None
            assert poll_setting.get_value() == 180

            max_concurrent = session.get(SystemSetting, "max_concurrent")
            assert max_concurrent is not None
            assert max_concurrent.get_value() == 2


class TestSettingsStatusEndpoint:
    """Tests for GET /api/v1/settings/status."""

    def test_settings_status_returns_connections(self, client: TestClient) -> None:
        """GET /settings/status returns connection health."""
        response = client.get("/api/v1/settings/status")
        assert response.status_code == 200

        data = response.json()
        assert "connections" in data
        assert len(data["connections"]) == 2

        services = {c["service"]: c for c in data["connections"]}
        assert "clickup" in services
        assert "github" in services

        # In test environment without env vars, should be unconfigured
        assert services["clickup"]["status"] in ("connected", "unconfigured")
        assert services["github"]["status"] in ("connected", "unconfigured")


class TestSwarmMonitoringEndpoints:
    """Tests for GET /api/v1/swarms/active and /completed."""

    def test_list_active_swarms_empty(self, client: TestClient) -> None:
        """GET /swarms/active returns empty list when no swarms running."""
        response = client.get("/api/v1/swarms/active")
        assert response.status_code == 200

        data = response.json()
        assert data["swarms"] == []

    def test_list_active_swarms_returns_running_only(self, client: TestClient) -> None:
        """GET /swarms/active only returns swarms with status 'running'."""
        # Create test swarms
        with session_scope() as session:
            running = SwarmInstance(
                task_id="task-1",
                task_name="Running Task",
                task_type="feature",
                branch="feature/task-1",
                status="running",
                active_agent="coder",
            )
            completed = SwarmInstance(
                task_id="task-2",
                task_name="Completed Task",
                task_type="feature",
                branch="feature/task-2",
                status="completed",
                active_agent=None,
            )
            session.add_all([running, completed])
            session.commit()

        response = client.get("/api/v1/swarms/active")
        assert response.status_code == 200

        data = response.json()
        assert len(data["swarms"]) == 1
        assert data["swarms"][0]["task_id"] == "task-1"
        assert data["swarms"][0]["status"] == "running"

    def test_list_completed_swarms(self, client: TestClient) -> None:
        """GET /swarms/completed returns completed/failed/timeout swarms."""
        # Create test swarms
        with session_scope() as session:
            completed = SwarmInstance(
                task_id="task-1",
                task_name="Completed Task",
                task_type="feature",
                branch="feature/task-1",
                status="completed",
            )
            failed = SwarmInstance(
                task_id="task-2",
                task_name="Failed Task",
                task_type="fix",
                branch="fix/task-2",
                status="failed",
            )
            running = SwarmInstance(
                task_id="task-3",
                task_name="Running Task",
                task_type="chore",
                branch="chore/task-3",
                status="running",
            )
            session.add_all([completed, failed, running])
            session.commit()

        response = client.get("/api/v1/swarms/completed")
        assert response.status_code == 200

        data = response.json()
        assert len(data["swarms"]) == 2  # completed + failed, not running

        statuses = {s["status"] for s in data["swarms"]}
        assert "completed" in statuses
        assert "failed" in statuses

    def test_list_completed_swarms_respects_limit(self, client: TestClient) -> None:
        """GET /swarms/completed respects the limit parameter."""
        # Create 10 completed swarms
        with session_scope() as session:
            for i in range(10):
                swarm = SwarmInstance(
                    task_id=f"task-{i}",
                    task_name=f"Task {i}",
                    task_type="feature",
                    branch=f"feature/task-{i}",
                    status="completed",
                )
                session.add(swarm)
            session.commit()

        response = client.get("/api/v1/swarms/completed?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert len(data["swarms"]) == 5

    def test_get_swarm_log_success(self, client: TestClient) -> None:
        """GET /swarms/{id}/log returns conversation log."""
        with session_scope() as session:
            swarm = SwarmInstance(
                task_id="task-1",
                task_name="Test Task",
                task_type="feature",
                branch="feature/task-1",
                status="completed",
                conversation_log="Agent 1: Hello\nAgent 2: Hi\nAgent 1: Done",
                pr_url="https://github.com/org/repo/pull/1",
            )
            session.add(swarm)
            session.commit()
            swarm_id = swarm.id

        response = client.get(f"/api/v1/swarms/{swarm_id}/log")
        assert response.status_code == 200

        data = response.json()
        assert data["task_id"] == "task-1"
        assert data["task_name"] == "Test Task"
        assert data["status"] == "completed"
        assert data["log"] == "Agent 1: Hello\nAgent 2: Hi\nAgent 1: Done"
        assert data["pr_url"] == "https://github.com/org/repo/pull/1"

    def test_get_swarm_log_not_found(self, client: TestClient) -> None:
        """GET /swarms/{id}/log returns 404 for non-existent swarm."""
        response = client.get("/api/v1/swarms/999/log")
        assert response.status_code == 404

    def test_get_swarm_log_null_log(self, client: TestClient) -> None:
        """GET /swarms/{id}/log handles null conversation log."""
        with session_scope() as session:
            swarm = SwarmInstance(
                task_id="task-1",
                task_name="Test Task",
                task_type="feature",
                branch="feature/task-1",
                status="running",
                conversation_log=None,
            )
            session.add(swarm)
            session.commit()
            swarm_id = swarm.id

        response = client.get(f"/api/v1/swarms/{swarm_id}/log")
        assert response.status_code == 200

        data = response.json()
        assert data["log"] is None

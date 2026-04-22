"""Tests for settings API endpoints (T064)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from syntexa.models import (
    SystemSetting,
    session_scope,
)


class TestSettingsEndpoints:
    """Tests for GET /api/v1/settings and PATCH /api/v1/settings."""

    def test_get_settings_returns_defaults(self, client: TestClient, auth_headers: dict) -> None:
        """GET /settings returns default values on first call."""
        response = client.get("/api/v1/settings", headers=auth_headers)
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

    def test_patch_settings_updates_values(self, client: TestClient, auth_headers: dict) -> None:
        """PATCH /settings updates runtime-tunable settings."""
        response = client.patch(
            "/api/v1/settings",
            json={"poll_interval": 120, "max_concurrent": 5},
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["poll_interval"] == 120
        assert data["max_concurrent"] == 5

    def test_patch_settings_validates_values(self, client: TestClient, auth_headers: dict) -> None:
        """PATCH /settings rejects invalid values."""
        # poll_interval too low
        response = client.patch(
            "/api/v1/settings",
            json={"poll_interval": 5},
            headers=auth_headers,
        )
        assert response.status_code == 422

        # max_concurrent too low
        response = client.patch(
            "/api/v1/settings",
            json={"max_concurrent": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422

        # log_retention_days too low
        response = client.patch(
            "/api/v1/settings",
            json={"log_retention_days": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_patch_settings_with_invalid_field_excluded(self, client: TestClient, auth_headers: dict) -> None:
        """PATCH /settings ignores unknown fields (not in schema)."""
        # repo_path is not in the update schema, so it's ignored
        response = client.patch(
            "/api/v1/settings",
            json={"repo_path": "/some/path"},
            headers=auth_headers,
        )
        # Results in empty update, hence "No settings provided"
        assert response.status_code == 400
        assert "No settings provided" in response.json()["detail"]

    def test_patch_settings_requires_at_least_one_field(self, client: TestClient, auth_headers: dict) -> None:
        """PATCH /settings requires at least one field to update."""
        response = client.patch("/api/v1/settings", json={}, headers=auth_headers)
        assert response.status_code == 400
        assert "No settings provided" in response.json()["detail"]

    def test_settings_persisted_to_database(self, client: TestClient, auth_headers: dict) -> None:
        """Settings updates are stored in the database."""
        client.patch(
            "/api/v1/settings",
            json={"poll_interval": 180, "max_concurrent": 2},
            headers=auth_headers,
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

    def test_settings_status_returns_connections(self, client: TestClient, auth_headers: dict) -> None:
        """GET /settings/status returns connection health."""
        response = client.get("/api/v1/settings/status", headers=auth_headers)
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



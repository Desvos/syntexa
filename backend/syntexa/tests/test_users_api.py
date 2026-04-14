"""Tests for user management endpoints (US5)."""
from __future__ import annotations

from fastapi.testclient import TestClient


class TestProtectedUsersEndpoint:
    """Tests that user endpoints require authentication."""

    def test_list_users_requires_auth(self, client: TestClient) -> None:
        """Test GET /users without auth returns 401."""
        response = client.get("/api/v1/users")
        assert response.status_code == 401

    def test_create_user_requires_auth(self, client: TestClient) -> None:
        """Test POST /users without auth returns 401."""
        response = client.post(
            "/api/v1/users",
            json={"username": "newuser", "password": "password123"},
        )
        assert response.status_code == 401

    def test_delete_user_requires_auth(self, client: TestClient) -> None:
        """Test DELETE /users/{id} without auth returns 401."""
        response = client.delete("/api/v1/users/1")
        assert response.status_code == 401

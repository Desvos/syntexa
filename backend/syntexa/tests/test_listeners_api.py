"""Tests for the /api/v1/listeners control endpoints."""
from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from syntexa.listeners import registry
from syntexa.listeners.base import Listener
from syntexa.listeners.event import InboundEvent


class _DummyListener(Listener):
    name = "dummy"

    def __init__(self, name: str = "dummy") -> None:
        super().__init__(poll_interval=0.05, error_backoff=0.05)
        self.name = name

    async def poll_once(self) -> list[InboundEvent]:
        return []

    async def process_event(self, event: InboundEvent) -> None:
        return None


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    """Clean registry state before each test + swap factories with dummies.

    We don't want real ClickUp / Telegram listeners to spin up in these
    API tests — they'd try to read credentials + hit the network.
    """
    registry.clear()
    registry.register_factory("clickup", lambda: _DummyListener("clickup"))
    registry.register_factory("telegram", lambda: _DummyListener("telegram"))
    yield
    # Stop anything that started
    try:
        asyncio.run(registry.stop_all())
    except Exception:
        pass
    registry.clear()


def test_get_status_shows_all_known_listeners_not_running(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.get("/api/v1/listeners", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "clickup" in body["listeners"]
    assert "telegram" in body["listeners"]
    assert body["listeners"]["clickup"]["running"] is False
    assert body["listeners"]["telegram"]["running"] is False


def test_start_single_listener_reports_running(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.post(
        "/api/v1/listeners/start",
        json={"name": "clickup"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["listeners"]["clickup"]["running"] is True
    assert body["listeners"]["telegram"]["running"] is False

    # Cleanup
    client.post(
        "/api/v1/listeners/stop",
        json={"name": "clickup"},
        headers=auth_headers,
    )


def test_start_all_and_stop_all(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.post(
        "/api/v1/listeners/start",
        json={"name": "all"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["listeners"]["clickup"]["running"] is True
    assert body["listeners"]["telegram"]["running"] is True

    resp = client.post(
        "/api/v1/listeners/stop",
        json={"name": "all"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["listeners"]["clickup"]["running"] is False
    assert body["listeners"]["telegram"]["running"] is False


def test_endpoints_require_auth(client: TestClient) -> None:
    assert client.get("/api/v1/listeners").status_code == 401
    assert (
        client.post(
            "/api/v1/listeners/start", json={"name": "clickup"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/listeners/stop", json={"name": "clickup"}
        ).status_code
        == 401
    )


def test_unknown_listener_rejected(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.post(
        "/api/v1/listeners/start",
        json={"name": "bogus"},
        headers=auth_headers,
    )
    # Pydantic Literal rejects with 422
    assert resp.status_code == 422

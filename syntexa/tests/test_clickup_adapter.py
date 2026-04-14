"""T030 — ClickUp adapter unit tests with mocked HTTP via httpx MockTransport."""
from __future__ import annotations

import json

import httpx
import pytest

from syntexa.adapters.clickup import CLICKUP_BASE_URL, AdapterError, ClickUpAdapter


def _client_with(handler) -> httpx.Client:
    return httpx.Client(
        base_url=CLICKUP_BASE_URL,
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "test-key"},
    )


def test_list_tasks_filters_by_tag() -> None:
    payload = {
        "tasks": [
            {
                "id": "A1",
                "name": "Feature X",
                "text_content": "Build it",
                "status": {"status": "in progress"},
                "tags": [{"name": "agent-swarm"}, {"name": "feature"}],
                "url": "https://clickup.example/A1",
            },
            {
                "id": "B2",
                "name": "Feature Y",
                "tags": [{"name": "other"}],
                "status": {"status": "open"},
            },
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/list/LIST_ID/task")
        assert request.headers["Authorization"] == "test-key"
        return httpx.Response(200, json=payload)

    adapter = ClickUpAdapter("test-key", "LIST_ID", client=_client_with(handler))
    tasks = adapter.list_tasks("agent-swarm")

    assert len(tasks) == 1
    assert tasks[0].id == "A1"
    assert tasks[0].name == "Feature X"
    assert "agent-swarm" in tasks[0].tags
    assert tasks[0].url == "https://clickup.example/A1"


def test_list_tasks_returns_empty_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"err": "boom"})

    adapter = ClickUpAdapter("k", "L", client=_client_with(handler))
    assert adapter.list_tasks("agent-swarm") == []


def test_update_status_maps_normalized_values() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={})

    adapter = ClickUpAdapter("k", "L", client=_client_with(handler))
    adapter.update_status("A1", "done")

    assert captured["method"] == "PUT"
    assert captured["path"].endswith("/task/A1")
    assert captured["body"] == {"status": "complete"}


def test_update_status_raises_adaptererror_on_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"err": "bad"})

    adapter = ClickUpAdapter("k", "L", client=_client_with(handler))
    with pytest.raises(AdapterError):
        adapter.update_status("A1", "in_progress")


def test_add_comment_posts_body() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={})

    adapter = ClickUpAdapter("k", "L", client=_client_with(handler))
    adapter.add_comment("A1", "hello")
    assert captured["path"].endswith("/task/A1/comment")
    assert captured["body"] == {"comment_text": "hello", "notify_all": False}


def test_health_check_ok_and_error() -> None:
    state = {"code": 200}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(state["code"], json={})

    adapter = ClickUpAdapter("k", "L", client=_client_with(handler))
    assert adapter.health_check() is True
    state["code"] = 401
    assert adapter.health_check() is False

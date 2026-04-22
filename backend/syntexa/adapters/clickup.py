"""ClickUp implementation of ProjectManagementAdapter.

Uses the REST API v2. Network errors are caught and re-raised as
`AdapterError` so the daemon can decide how to react without depending on
httpx internals.
"""
from __future__ import annotations

import logging
from typing import override

import httpx

from syntexa.adapters.base import ProjectManagementAdapter, TaskRef, TaskStatus

logger = logging.getLogger(__name__)

CLICKUP_BASE_URL = "https://api.clickup.com/api/v2"

# Normalized → ClickUp display names. Projects can override by re-mapping.
DEFAULT_STATUS_MAP: dict[str, str] = {
    "open": "open",
    "in_progress": "in progress",
    "blocked": "blocked",
    "done": "complete",
    "error": "to do",  # revert on failure
}


class AdapterError(RuntimeError):
    """Raised when a remote call fails in a way the daemon must handle."""


class ClickUpAdapter(ProjectManagementAdapter):
    def __init__(
        self,
        api_key: str,
        list_id: str,
        *,
        status_map: dict[str, str] | None = None,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("ClickUpAdapter requires an API key.")
        if not list_id:
            raise ValueError("ClickUpAdapter requires a list_id.")
        self._list_id = list_id
        self._status_map = {**DEFAULT_STATUS_MAP, **(status_map or {})}
        self._client = client or httpx.Client(
            base_url=CLICKUP_BASE_URL,
            headers={"Authorization": api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )

    @override
    def __hash__(self) -> int:
        return hash((self._list_id, id(self._client)))

    def close(self) -> None:
        self._client.close()

    def list_tasks(self, tag: str) -> list[TaskRef]:
        try:
            resp = self._client.get(
                f"/list/{self._list_id}/task",
                params={"archived": "false", "subtasks": "false"},
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("ClickUp list_tasks failed; returning empty list")
            return []

        payload = resp.json()
        out: list[TaskRef] = []
        for task in payload.get("tasks", []):
            tag_names = tuple(t.get("name", "") for t in task.get("tags", []))
            if tag not in tag_names:
                continue
            out.append(
                TaskRef(
                    id=str(task["id"]),
                    name=task.get("name", ""),
                    description=task.get("text_content") or task.get("description") or "",
                    tags=tag_names,
                    status=(task.get("status") or {}).get("status", ""),
                    url=task.get("url"),
                )
            )
        return out

    def update_status(self, task_id: str, status: TaskStatus) -> None:
        mapped = self._status_map.get(status)
        if mapped is None:
            raise ValueError(f"No ClickUp mapping for normalized status '{status}'")
        try:
            resp = self._client.put(f"/task/{task_id}", json={"status": mapped})
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise AdapterError(f"ClickUp update_status({task_id}) failed") from exc

    def add_comment(self, task_id: str, body: str) -> None:
        try:
            resp = self._client.post(
                f"/task/{task_id}/comment",
                json={"comment_text": body, "notify_all": False},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise AdapterError(f"ClickUp add_comment({task_id}) failed") from exc

    def health_check(self) -> bool:
        try:
            resp = self._client.get("/user")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

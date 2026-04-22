"""Listener control API.

Three endpoints:

- ``GET  /listeners``        → status snapshot for every known listener
- ``POST /listeners/start``  → start one or all listeners
- ``POST /listeners/stop``   → stop one or all listeners

Listeners are deliberately NOT started by the FastAPI lifespan — the
operator toggles them from the UI. This avoids hammering upstream APIs
on every app reload and lets the test suite import the app without any
credentials wired up.
"""
from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from syntexa.listeners import registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/listeners", tags=["listeners"])


class ListenerControlRequest(BaseModel):
    """Body for start/stop. ``"all"`` fans out to every known listener."""

    name: Literal["clickup", "telegram", "all"] = Field(...)


class ListenerStatus(BaseModel):
    name: str
    running: bool
    last_poll_at: str | None = None
    last_error: str | None = None


class ListenerStatusResponse(BaseModel):
    listeners: dict[str, ListenerStatus]


def _as_response(status_map: dict[str, dict[str, object]]) -> ListenerStatusResponse:
    return ListenerStatusResponse(
        listeners={
            k: ListenerStatus(
                name=str(v.get("name", k)),
                running=bool(v.get("running", False)),
                last_poll_at=(
                    str(v["last_poll_at"])
                    if v.get("last_poll_at") is not None
                    else None
                ),
                last_error=(
                    str(v["last_error"])
                    if v.get("last_error") is not None
                    else None
                ),
            )
            for k, v in status_map.items()
        }
    )


@router.get("", response_model=ListenerStatusResponse)
async def get_listener_status() -> ListenerStatusResponse:
    return _as_response(registry.status())


@router.post(
    "/start", response_model=ListenerStatusResponse, status_code=status.HTTP_200_OK
)
async def start_listener(payload: ListenerControlRequest) -> ListenerStatusResponse:
    try:
        if payload.name == "all":
            await registry.start_all()
        else:
            await registry.start_listener(payload.name)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from None
    return _as_response(registry.status())


@router.post(
    "/stop", response_model=ListenerStatusResponse, status_code=status.HTTP_200_OK
)
async def stop_listener(payload: ListenerControlRequest) -> ListenerStatusResponse:
    if payload.name == "all":
        await registry.stop_all()
    else:
        await registry.stop_listener(payload.name)
    return _as_response(registry.status())

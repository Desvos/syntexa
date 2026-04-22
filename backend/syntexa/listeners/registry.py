"""Process-wide registry of running listeners.

Kept dead simple on purpose: a module-level dict keyed by listener name,
an asyncio.Lock to serialize start/stop (prevents two concurrent
/listeners/start calls from double-starting the same listener), and
factory functions that lazily construct each known listener.

Lifespan integration:
- The API does NOT auto-start listeners — the user explicitly POSTs to
  /listeners/start. So this registry lives in-process and only goes
  away on process shutdown.
- If you add a new listener type, register it in ``_FACTORIES`` and
  it becomes available under its key via the control API.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Callable

from syntexa.listeners.base import Listener

logger = logging.getLogger(__name__)


# Lazy — we want test isolation: each test that imports the module gets
# a clean registry, and real listener construction (which may hit
# credentials) doesn't happen until start() is called.
_LISTENERS: dict[str, Listener] = {}
_LOCK = asyncio.Lock()


def _make_clickup_listener() -> Listener:
    """Factory for the ClickUp listener; imported lazily to dodge cycles."""
    from syntexa.listeners.clickup_listener import ClickUpListener

    return ClickUpListener()


def _make_telegram_listener() -> Listener:
    from syntexa.listeners.telegram_listener import TelegramListener

    return TelegramListener()


_FACTORIES: dict[str, Callable[[], Listener]] = {
    "clickup": _make_clickup_listener,
    "telegram": _make_telegram_listener,
}


def known_listener_names() -> list[str]:
    return list(_FACTORIES.keys())


def register_factory(name: str, factory: Callable[[], Listener]) -> None:
    """Override/add a factory. Tests use this to inject mocks.

    We do NOT eagerly build the listener — it's built on the first
    ``start_listener`` call. That keeps the registry idle-safe.
    """
    _FACTORIES[name] = factory


def clear() -> None:
    """Reset the registry. Tests only — leaves already-running listeners
    orphaned, which is fine in a test process that's about to exit."""
    _LISTENERS.clear()


def _get_or_build(name: str) -> Listener:
    listener = _LISTENERS.get(name)
    if listener is None:
        factory = _FACTORIES.get(name)
        if factory is None:
            raise KeyError(f"Unknown listener: {name!r}")
        listener = factory()
        _LISTENERS[name] = listener
    return listener


async def start_listener(name: str) -> Listener:
    """Start a specific listener by name. Returns the instance."""
    async with _LOCK:
        listener = _get_or_build(name)
        await listener.start()
        return listener


async def stop_listener(name: str) -> None:
    async with _LOCK:
        listener = _LISTENERS.get(name)
        if listener is not None:
            await listener.stop()


async def start_all() -> dict[str, Listener]:
    """Start every registered listener."""
    started: dict[str, Listener] = {}
    for name in known_listener_names():
        started[name] = await start_listener(name)
    return started


async def stop_all() -> None:
    for name in list(_LISTENERS.keys()):
        await stop_listener(name)


def status() -> dict[str, dict[str, object]]:
    """Status map for the API. Includes known-but-never-started listeners
    as ``running: False`` so the frontend can show all available names."""
    out: dict[str, dict[str, object]] = {}
    for name in known_listener_names():
        listener = _LISTENERS.get(name)
        if listener is None:
            out[name] = {
                "name": name,
                "running": False,
                "last_poll_at": None,
                "last_error": None,
            }
        else:
            out[name] = listener.status()
    return out

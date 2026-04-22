"""Base asyncio listener loop.

Every concrete listener (ClickUp, Telegram, ...) subclasses ``Listener``
and implements:

- ``poll_once()``: ask the upstream system for new items and return a
  list of ``InboundEvent`` objects. MUST be idempotent — the base class
  dedups by external_id at a higher layer (``ProcessedEvent`` table in
  ``process_event``).
- ``process_event()``: do something with one event (typically: create a
  Swarm row + kick off ``run_swarm``).

The base class owns the lifecycle: ``start`` spawns a long-running task
that calls ``poll_once`` every ``poll_interval`` seconds, hands each
event to ``process_event`` in order, and backs off on errors. ``stop``
cancels the task and awaits it to unwind cleanly.

Running state is reported via ``status()``, which the registry bubbles
up to the API. ``last_poll_at`` / ``last_error`` make debugging a dead
listener over the wire possible without SSH'ing into the host.
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from syntexa.listeners.event import InboundEvent

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Listener(ABC):
    """Asyncio-driven polling listener.

    Subclasses override ``poll_once`` and ``process_event``. The base
    class provides lifecycle management: start/stop, error backoff,
    status introspection.

    ``poll_interval`` is the sleep between polls on the happy path.
    ``error_backoff`` is the starting sleep after a poll failure; it
    doubles up to ``max_backoff`` on consecutive failures and resets on
    success. Keeps us from hammering a down upstream.
    """

    #: Human-readable name, surfaced via ``status()`` and the control API.
    name: str = "listener"

    def __init__(
        self,
        *,
        poll_interval: float = 30.0,
        error_backoff: float = 5.0,
        max_backoff: float = 300.0,
    ) -> None:
        self.poll_interval = poll_interval
        self.error_backoff = error_backoff
        self.max_backoff = max_backoff

        self._task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None
        self._last_poll_at: datetime | None = None
        self._last_error: str | None = None

    # --- subclass contract ------------------------------------------------

    @abstractmethod
    async def poll_once(self) -> list[InboundEvent]:
        """Fetch new events from the upstream source.

        Implementations MUST return fast-ish (this is called on a wall
        clock) and should NOT raise — network errors should be caught
        and logged, returning ``[]`` on failure. If the method does
        raise, the base loop catches it and enters error backoff.
        """

    @abstractmethod
    async def process_event(self, event: InboundEvent) -> None:
        """Act on a single inbound event (usually: create + run a swarm).

        Dedup via ``ProcessedEvent`` lives here, not in ``poll_once``,
        so ``poll_once`` can stay idempotent without caring about state.
        """

    # --- lifecycle --------------------------------------------------------

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        """Spawn the poll loop. Idempotent — no-op if already running."""
        if self.is_running():
            return
        self._stop_event = asyncio.Event()
        self._last_error = None
        self._task = asyncio.create_task(
            self._run_loop(), name=f"listener:{self.name}"
        )

    async def stop(self, timeout: float = 10.0) -> None:
        """Signal the loop to exit and wait for it.

        We use an ``asyncio.Event`` rather than ``task.cancel()`` so
        in-flight ``process_event`` calls finish cleanly (avoids leaving
        half-created swarms behind). If the task doesn't honor the stop
        in time we fall back to cancel + shield.
        """
        if not self.is_running():
            return
        assert self._stop_event is not None
        assert self._task is not None
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._task, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(
                "Listener %s did not stop within %.1fs; cancelling",
                self.name,
                timeout,
            )
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        finally:
            self._task = None
            self._stop_event = None

    def status(self) -> dict[str, object]:
        """Snapshot dict consumed by the registry + API."""
        return {
            "name": self.name,
            "running": self.is_running(),
            "last_poll_at": (
                self._last_poll_at.isoformat()
                if self._last_poll_at is not None
                else None
            ),
            "last_error": self._last_error,
        }

    # --- internals --------------------------------------------------------

    async def _run_loop(self) -> None:
        """The actual poll/process/sleep/backoff cycle.

        One tick of the loop:
          1. call ``poll_once``
          2. for each event, call ``process_event`` (errors here don't
             kill the loop — we log and move on so one poison event
             can't stop the listener)
          3. sleep ``poll_interval`` unless stop was signalled

        On ``poll_once`` failure we bump an exponential backoff counter,
        then sleep that instead. Success resets it to the configured
        ``error_backoff``.
        """
        assert self._stop_event is not None
        current_backoff = self.error_backoff
        while not self._stop_event.is_set():
            poll_failed = False
            try:
                events = await self.poll_once()
                self._last_poll_at = _utcnow()
                self._last_error = None
                current_backoff = self.error_backoff
            except Exception as exc:  # noqa: BLE001 — log-and-continue
                self._last_error = f"poll_once: {exc!r}"
                logger.exception(
                    "Listener %s poll_once failed; backing off %.1fs",
                    self.name,
                    current_backoff,
                )
                events = []
                poll_failed = True

            for event in events:
                if self._stop_event.is_set():
                    break
                try:
                    await self.process_event(event)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "Listener %s process_event failed for %s/%s: %r",
                        self.name,
                        event.source,
                        event.external_id,
                        exc,
                    )
                    self._last_error = (
                        f"process_event[{event.external_id}]: {exc!r}"
                    )

            sleep_for = current_backoff if poll_failed else self.poll_interval
            if poll_failed:
                current_backoff = min(current_backoff * 2.0, self.max_backoff)

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=sleep_for
                )
            except asyncio.TimeoutError:
                # normal — we slept the full interval, keep polling
                continue

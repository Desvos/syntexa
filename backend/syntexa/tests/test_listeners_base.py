"""Tests for the base Listener lifecycle + error backoff."""
from __future__ import annotations

import asyncio

from syntexa.listeners.base import Listener
from syntexa.listeners.event import InboundEvent


class _Recorder(Listener):
    """Test double that emits preset event lists and records process_event calls."""

    name = "recorder"

    def __init__(
        self,
        scripted_polls: list[list[InboundEvent] | Exception],
        *,
        poll_interval: float = 0.01,
        error_backoff: float = 0.01,
        max_backoff: float = 0.05,
    ) -> None:
        super().__init__(
            poll_interval=poll_interval,
            error_backoff=error_backoff,
            max_backoff=max_backoff,
        )
        self._scripted = list(scripted_polls)
        self.processed: list[InboundEvent] = []
        self.poll_count = 0
        self.process_raise_on: set[str] = set()

    async def poll_once(self) -> list[InboundEvent]:
        self.poll_count += 1
        if not self._scripted:
            return []
        item = self._scripted.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def process_event(self, event: InboundEvent) -> None:
        if event.external_id in self.process_raise_on:
            raise RuntimeError(f"boom on {event.external_id}")
        self.processed.append(event)


def _ev(id_: str) -> InboundEvent:
    return InboundEvent(
        source="clickup", external_id=id_, title=f"t-{id_}", body=""
    )


async def test_start_then_stop_is_idempotent_and_runs_poll() -> None:
    listener = _Recorder([[_ev("1"), _ev("2")]])
    await listener.start()
    await listener.start()  # idempotent
    assert listener.is_running() is True

    # Let the loop process at least one poll.
    for _ in range(50):
        if len(listener.processed) >= 2:
            break
        await asyncio.sleep(0.01)

    await listener.stop()
    await listener.stop()  # idempotent
    assert listener.is_running() is False
    assert [e.external_id for e in listener.processed] == ["1", "2"]


async def test_error_in_poll_triggers_backoff_then_recovers() -> None:
    listener = _Recorder(
        [RuntimeError("upstream down"), [_ev("a")]]
    )
    await listener.start()
    for _ in range(100):
        if listener.processed:
            break
        await asyncio.sleep(0.01)
    await listener.stop()

    status = listener.status()
    # After recovery we cleared last_error; but we should have seen at
    # least 2 polls.
    assert listener.poll_count >= 2
    assert status["running"] is False
    assert [e.external_id for e in listener.processed] == ["a"]


async def test_process_event_error_does_not_kill_loop() -> None:
    listener = _Recorder(
        [[_ev("good1"), _ev("bad"), _ev("good2")]]
    )
    listener.process_raise_on = {"bad"}
    await listener.start()
    for _ in range(100):
        if len(listener.processed) >= 2:
            break
        await asyncio.sleep(0.01)
    await listener.stop()
    ids = [e.external_id for e in listener.processed]
    assert "good1" in ids and "good2" in ids
    assert "bad" not in ids
    assert listener.status()["last_error"] is not None


async def test_status_reports_running_and_last_poll() -> None:
    listener = _Recorder([[]])
    assert listener.is_running() is False
    assert listener.status()["last_poll_at"] is None

    await listener.start()
    for _ in range(50):
        if listener.poll_count >= 1:
            break
        await asyncio.sleep(0.01)
    status_snapshot = listener.status()
    assert status_snapshot["running"] is True
    assert status_snapshot["last_poll_at"] is not None

    await listener.stop()

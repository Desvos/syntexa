"""Tests for ClickUpListener with a mocked adapter + fake run_swarm.

We bypass httpx entirely by swapping ``adapter_factory`` for a fake
that returns canned ``TaskRef`` lists. ``run_swarm`` is replaced with a
recorder so we can assert it was called exactly once per new swarm.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from cryptography.fernet import Fernet
import pytest
from sqlalchemy.orm import Session

from syntexa.adapters.base import TaskRef
from syntexa.core import crypto
from syntexa.listeners.clickup_listener import ClickUpListener
from syntexa.models import (
    Agent,
    ExternalCredential,
    LLMProvider,
    ProcessedEvent,
    Repository,
    Swarm,
)


@pytest.fixture(autouse=True)
def _isolated_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYNTEXA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    crypto.reset_cache_for_tests()


class _FakeAdapter:
    def __init__(self, tasks_by_list: dict[str, list[TaskRef]]) -> None:
        self._tasks_by_list = tasks_by_list
        self.calls: list[tuple[str, str]] = []
        # set by factory for the current call:
        self._current_list_id: str = ""

    def list_tasks(self, tag: str) -> list[TaskRef]:
        self.calls.append((self._current_list_id, tag))
        return self._tasks_by_list.get(self._current_list_id, [])


def _seed_db(db: Session) -> tuple[Repository, Repository]:
    """Create two repos (one tagged, one untagged), one provider, two agents.

    Returns the two Repository rows. The first has a clickup_list_id;
    the second does not (used to check the listener skips it).
    """
    provider = LLMProvider(
        name="p1",
        provider_type="openai",
        api_key_encrypted=crypto.encrypt("sk-x"),
        default_model="gpt-4o-mini",
    )
    db.add(provider)
    db.flush()

    agents = [
        Agent(
            name="alice",
            system_prompt="You are alice.",
            provider_id=provider.id,
            is_active=True,
        ),
        Agent(
            name="bob",
            system_prompt="You are bob.",
            provider_id=provider.id,
            is_active=True,
        ),
    ]
    db.add_all(agents)

    repo_watched = Repository(
        name="watched",
        path="/tmp/watched",
        clickup_list_id="LIST_1",
    )
    repo_ignored = Repository(
        name="ignored",
        path="/tmp/ignored",
        clickup_list_id=None,
    )
    db.add_all([repo_watched, repo_ignored])

    cred = ExternalCredential(service_type="clickup", is_active=True)
    cred.set_credentials({"api_key": "pk_test", "list_id": "LIST_1"})
    db.add(cred)
    db.flush()

    return repo_watched, repo_ignored


def _make_listener(
    db_session: Session,
    adapter: _FakeAdapter,
    run_swarm_calls: list[int],
) -> ClickUpListener:
    @contextmanager
    def _session_factory() -> Iterator[Session]:
        # Share ONE session across all listener ops so they see each
        # other's writes without commits muddling our test DB setup.
        try:
            yield db_session
            db_session.flush()
        except Exception:
            db_session.rollback()
            raise

    def _factory(api_key: str, list_id: str) -> _FakeAdapter:
        adapter._current_list_id = list_id
        return adapter

    def _run_swarm(swarm_id: int, *args: Any, **kwargs: Any) -> Any:
        run_swarm_calls.append(swarm_id)

        class _R:
            agent_outputs: dict[int, str] = {}

        return _R()

    return ClickUpListener(
        adapter_factory=_factory,
        run_swarm_impl=_run_swarm,
        session_factory=_session_factory,
    )


async def test_polls_only_tagged_repos_and_creates_swarm(
    db_session: Session,
) -> None:
    watched, _ignored = _seed_db(db_session)

    tasks = {
        "LIST_1": [
            TaskRef(
                id="TASK_A",
                name="Fix login bug",
                description="Details here",
                tags=("syntexa-auto",),
                status="open",
                url="https://clickup/TASK_A",
            )
        ]
    }
    adapter = _FakeAdapter(tasks)
    runs: list[int] = []
    listener = _make_listener(db_session, adapter, runs)

    events = await listener.poll_once()
    assert len(events) == 1
    assert events[0].source == "clickup"
    assert events[0].external_id == "TASK_A"
    assert events[0].repository_id == watched.id

    # The ignored repo (no clickup_list_id) wasn't polled.
    assert len(adapter.calls) == 1
    assert adapter.calls[0] == ("LIST_1", "syntexa-auto")

    await listener.process_event(events[0])
    # We need to let the fire-and-forget run_swarm task execute.
    import asyncio as _asyncio

    for _ in range(50):
        if runs:
            break
        await _asyncio.sleep(0.01)

    # Swarm + ProcessedEvent created
    swarms = db_session.query(Swarm).all()
    assert len(swarms) == 1
    assert swarms[0].repository_id == watched.id
    assert "Fix login bug" in (swarms[0].task_description or "")

    pe = db_session.get(ProcessedEvent, ("clickup", "TASK_A"))
    assert pe is not None
    assert pe.swarm_id == swarms[0].id

    # run_swarm called exactly once with the new swarm id.
    assert runs == [swarms[0].id]


async def test_dedup_skips_already_processed_event(
    db_session: Session,
) -> None:
    watched, _ = _seed_db(db_session)
    tasks = {
        "LIST_1": [
            TaskRef(
                id="TASK_B",
                name="Already done",
                description="",
                tags=("syntexa-auto",),
                status="open",
                url=None,
            )
        ]
    }
    adapter = _FakeAdapter(tasks)
    runs: list[int] = []
    listener = _make_listener(db_session, adapter, runs)

    events = await listener.poll_once()
    assert len(events) == 1

    # First processing creates a swarm
    await listener.process_event(events[0])
    import asyncio as _asyncio

    for _ in range(50):
        if runs:
            break
        await _asyncio.sleep(0.01)
    first_count = db_session.query(Swarm).count()
    assert first_count == 1

    # Second processing of the SAME external_id is a no-op
    await listener.process_event(events[0])
    for _ in range(20):
        await _asyncio.sleep(0.01)
    assert db_session.query(Swarm).count() == first_count
    assert runs == [db_session.query(Swarm).first().id]


async def test_poll_handles_list_tasks_exception_gracefully(
    db_session: Session,
) -> None:
    _seed_db(db_session)

    class _ExplodingAdapter(_FakeAdapter):
        def list_tasks(self, tag: str) -> list[TaskRef]:
            raise RuntimeError("ClickUp is on fire")

    adapter = _ExplodingAdapter({})
    runs: list[int] = []
    listener = _make_listener(db_session, adapter, runs)

    events = await listener.poll_once()
    # Should swallow the adapter error and return []
    assert events == []
    assert runs == []


async def test_custom_trigger_tag_per_repo(db_session: Session) -> None:
    watched, _ = _seed_db(db_session)
    watched.clickup_trigger_tag = "custom-tag"
    db_session.flush()

    tasks = {
        "LIST_1": [
            TaskRef(
                id="TASK_C",
                name="Custom",
                description="",
                tags=("custom-tag",),
                status="open",
                url=None,
            )
        ]
    }
    adapter = _FakeAdapter(tasks)
    runs: list[int] = []
    listener = _make_listener(db_session, adapter, runs)

    events = await listener.poll_once()
    assert events
    assert adapter.calls == [("LIST_1", "custom-tag")]


async def test_no_credentials_returns_empty(db_session: Session) -> None:
    # Seed repos + agents but NO ExternalCredential
    provider = LLMProvider(
        name="p1",
        provider_type="openai",
        api_key_encrypted=crypto.encrypt("sk-x"),
        default_model="gpt-4o-mini",
    )
    db_session.add(provider)
    db_session.flush()
    repo = Repository(
        name="r1", path="/tmp/r1", clickup_list_id="LIST_1"
    )
    db_session.add(repo)
    db_session.flush()

    adapter = _FakeAdapter({})
    runs: list[int] = []
    listener = _make_listener(db_session, adapter, runs)

    events = await listener.poll_once()
    assert events == []
    assert adapter.calls == []

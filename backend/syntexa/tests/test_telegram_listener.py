"""Tests for TelegramListener with a fake Telegram HTTP client."""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from typing import Any, Iterator

from cryptography.fernet import Fernet
import pytest
from sqlalchemy.orm import Session

from syntexa.core import crypto
from syntexa.listeners.telegram_listener import TelegramListener
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


class _FakeTelegramClient:
    def __init__(self, scripted_updates: list[list[dict[str, Any]]]) -> None:
        self._scripted = list(scripted_updates)
        self.sent: list[tuple[int, str]] = []

    def get_updates(
        self, offset: int | None = None, timeout: int = 0
    ) -> list[dict[str, Any]]:
        if not self._scripted:
            return []
        return self._scripted.pop(0)

    def send_message(self, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))


def _seed(db: Session, *, allowed_chat: int = 111, default_repo: bool = True) -> Repository:
    provider = LLMProvider(
        name="p1",
        provider_type="openai",
        api_key_encrypted=crypto.encrypt("sk-x"),
        default_model="gpt-4o-mini",
    )
    db.add(provider)
    db.flush()
    db.add(
        Agent(
            name="alice",
            system_prompt="You are alice.",
            provider_id=provider.id,
            is_active=True,
        )
    )
    repo = Repository(name="myrepo", path="/tmp/myrepo")
    db.add(repo)
    db.flush()

    cred = ExternalCredential(service_type="telegram", is_active=True)
    payload: dict[str, Any] = {
        "bot_token": "TOKEN",
        "allowed_chat_ids": [allowed_chat],
    }
    if default_repo:
        payload["default_repository_id"] = repo.id
    cred.set_credentials(payload)
    db.add(cred)
    db.flush()
    return repo


def _make_listener(
    db_session: Session,
    client: _FakeTelegramClient,
    run_swarm_calls: list[int],
) -> TelegramListener:
    @contextmanager
    def _session_factory() -> Iterator[Session]:
        try:
            yield db_session
            db_session.flush()
        except Exception:
            db_session.rollback()
            raise

    def _run_swarm(swarm_id: int, *args: Any, **kwargs: Any) -> Any:
        run_swarm_calls.append(swarm_id)

        class _R:
            agent_outputs: dict[int, str] = {1: "ok"}

        return _R()

    return TelegramListener(
        client_factory=lambda _token: client,
        run_swarm_impl=_run_swarm,
        session_factory=_session_factory,
    )


def _msg(update_id: int, chat_id: int, text: str, msg_id: int = 1) -> dict[str, Any]:
    return {
        "update_id": update_id,
        "message": {
            "message_id": msg_id,
            "chat": {"id": chat_id},
            "text": text,
        },
    }


async def test_processes_allowed_chat_message_creates_swarm(
    db_session: Session,
) -> None:
    repo = _seed(db_session, allowed_chat=111)
    updates = [[_msg(100, 111, "Refactor the auth module")]]
    client = _FakeTelegramClient(updates)
    runs: list[int] = []
    listener = _make_listener(db_session, client, runs)

    events = await listener.poll_once()
    assert len(events) == 1
    assert events[0].source == "telegram"
    assert events[0].external_id == "100"
    assert events[0].repository_id == repo.id

    await listener.process_event(events[0])
    for _ in range(100):
        if runs:
            break
        await asyncio.sleep(0.01)

    swarms = db_session.query(Swarm).all()
    assert len(swarms) == 1
    assert swarms[0].repository_id == repo.id
    assert "Refactor the auth module" in (swarms[0].task_description or "")
    pe = db_session.get(ProcessedEvent, ("telegram", "100"))
    assert pe is not None and pe.swarm_id == swarms[0].id

    assert runs == [swarms[0].id]
    # At least the initial "spawned" reply was sent; possibly a summary too.
    assert any("spawned swarm" in t for _c, t in client.sent)


async def test_ignores_disallowed_chat_ids(db_session: Session) -> None:
    _seed(db_session, allowed_chat=111)
    # update from chat 999 (not allowed) must be silently dropped
    updates = [[_msg(200, 999, "Ignored task")]]
    client = _FakeTelegramClient(updates)
    runs: list[int] = []
    listener = _make_listener(db_session, client, runs)

    events = await listener.poll_once()
    assert events == []
    assert runs == []


async def test_dedup_by_update_id(db_session: Session) -> None:
    _seed(db_session, allowed_chat=111)
    updates = [[_msg(300, 111, "First")], [_msg(300, 111, "First")]]
    client = _FakeTelegramClient(updates)
    runs: list[int] = []
    listener = _make_listener(db_session, client, runs)

    events1 = await listener.poll_once()
    assert len(events1) == 1
    await listener.process_event(events1[0])
    for _ in range(50):
        if runs:
            break
        await asyncio.sleep(0.01)
    assert db_session.query(Swarm).count() == 1

    # Second poll returns same update_id → process_event must dedup
    events2 = await listener.poll_once()
    if events2:
        await listener.process_event(events2[0])
    for _ in range(20):
        await asyncio.sleep(0.01)
    assert db_session.query(Swarm).count() == 1
    assert runs == [db_session.query(Swarm).first().id]


async def test_slash_run_command_selects_repo_by_name(
    db_session: Session,
) -> None:
    _seed(db_session, allowed_chat=111)
    # Create a second repo
    other = Repository(name="otherrepo", path="/tmp/other")
    db_session.add(other)
    db_session.flush()

    updates = [[_msg(400, 111, "/run otherrepo Fix the CI")]]
    client = _FakeTelegramClient(updates)
    runs: list[int] = []
    listener = _make_listener(db_session, client, runs)

    events = await listener.poll_once()
    assert len(events) == 1
    assert events[0].repository_id == other.id
    assert events[0].body == "Fix the CI"

    await listener.process_event(events[0])
    for _ in range(50):
        if runs:
            break
        await asyncio.sleep(0.01)
    swarm = db_session.query(Swarm).first()
    assert swarm is not None
    assert swarm.repository_id == other.id


async def test_no_credentials_returns_empty(db_session: Session) -> None:
    updates = [[_msg(500, 111, "ignored")]]
    client = _FakeTelegramClient(updates)
    runs: list[int] = []
    listener = _make_listener(db_session, client, runs)

    events = await listener.poll_once()
    assert events == []
    assert runs == []

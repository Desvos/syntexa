"""Telegram bot listener — auto-spawns swarms from chat messages.

Uses Telegram's Bot API ``getUpdates`` endpoint as a long-poll. Auth +
config live in ``ExternalCredential`` with ``service_type="telegram"``:

    {
        "bot_token": "123456:ABC...",
        "allowed_chat_ids": [12345, 67890],
        "default_repository_id": 1,       # optional
    }

Message parsing:
- ``/run <repo_name> <task text>`` → look up repo by name, task text is
  the rest. If ``repo_name`` has no match, we fall back to
  ``default_repository_id``.
- Any other message → use ``default_repository_id``; task text is the
  entire message body.

Messages from chat ids NOT in ``allowed_chat_ids`` are ignored silently.
Dedup is on Telegram's ``update_id`` (monotonically increasing), and we
also persist the last-seen ``update_id`` offset to short-circuit
getUpdates — but ProcessedEvent is the authoritative dedup.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Callable

import httpx
from sqlalchemy.orm import Session

from syntexa.listeners.base import Listener
from syntexa.listeners.event import InboundEvent
from syntexa.models import (
    Agent,
    ExternalCredential,
    ProcessedEvent,
    Repository,
    Swarm,
    SwarmAgent,
)
from syntexa.models.database import session_scope

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"

RunSwarmCallable = Callable[..., object]


def _slugify(value: str, *, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not s:
        s = "task"
    return s[:max_len]


class TelegramClient:
    """Thin wrapper around the Bot HTTP API.

    Split out so tests can replace it wholesale with an httpx MockTransport.
    """

    def __init__(
        self,
        bot_token: str,
        *,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._bot_token = bot_token
        self._client = client or httpx.Client(
            base_url=f"{TELEGRAM_API}/bot{bot_token}",
            timeout=timeout,
        )

    def get_updates(
        self, offset: int | None = None, timeout: int = 0
    ) -> list[dict[str, Any]]:
        params: dict[str, int] = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        try:
            resp = self._client.get("/getUpdates", params=params)
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Telegram getUpdates failed")
            return []
        payload = resp.json()
        if not payload.get("ok"):
            return []
        return list(payload.get("result", []))

    def send_message(self, chat_id: int, text: str) -> None:
        try:
            resp = self._client.post(
                "/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Telegram sendMessage failed")


class TelegramListener(Listener):
    name = "telegram"

    def __init__(
        self,
        *,
        poll_interval: float = 5.0,
        error_backoff: float = 5.0,
        max_backoff: float = 120.0,
        client_factory: Callable[[str], TelegramClient] | None = None,
        run_swarm_impl: RunSwarmCallable | None = None,
        session_factory: Callable[[], Session] | None = None,
    ) -> None:
        super().__init__(
            poll_interval=poll_interval,
            error_backoff=error_backoff,
            max_backoff=max_backoff,
        )
        self._client_factory = client_factory or (
            lambda token: TelegramClient(token)
        )
        if run_swarm_impl is None:
            from syntexa.orchestrator.executor import run_swarm as _rs

            run_swarm_impl = _rs
        self._run_swarm = run_swarm_impl
        self._session_factory = session_factory
        # In-memory update offset — dedup table is the source of truth,
        # this is just a perf hint for getUpdates.
        self._update_offset: int | None = None

    # --- helpers ----------------------------------------------------------

    def _session(self):
        if self._session_factory is not None:
            return self._session_factory()
        return session_scope()

    def _load_config(
        self, db: Session
    ) -> tuple[str | None, set[int], int | None]:
        cred = (
            db.query(ExternalCredential)
            .filter_by(service_type="telegram", is_active=True)
            .order_by(ExternalCredential.id.asc())
            .first()
        )
        if cred is None:
            return None, set(), None
        data = cred.get_credentials()
        token = data.get("bot_token")
        allowed = {int(x) for x in data.get("allowed_chat_ids", [])}
        default_repo = data.get("default_repository_id")
        if default_repo is not None:
            try:
                default_repo = int(default_repo)
            except (TypeError, ValueError):
                default_repo = None
        return token, allowed, default_repo

    def _resolve_repo_and_task(
        self,
        db: Session,
        text: str,
        default_repository_id: int | None,
    ) -> tuple[int | None, str]:
        """Parse ``/run <repo> <task>`` or fall back to default."""
        stripped = text.strip()
        if stripped.startswith("/run"):
            parts = stripped.split(None, 2)
            if len(parts) >= 3:
                repo_name, task_text = parts[1], parts[2]
                repo = (
                    db.query(Repository)
                    .filter(Repository.name == repo_name)
                    .first()
                )
                if repo is not None:
                    return repo.id, task_text
            # /run but no repo match → fall through to default
            rest = parts[1] if len(parts) == 2 else ""
            return default_repository_id, rest or stripped
        return default_repository_id, stripped

    # --- Listener API -----------------------------------------------------

    async def poll_once(self) -> list[InboundEvent]:
        def _blocking() -> list[InboundEvent]:
            with self._session() as db:
                token, allowed, default_repo = self._load_config(db)
                if not token:
                    logger.debug("Telegram listener: no bot_token; skipping")
                    return []

                client = self._client_factory(token)
                updates = client.get_updates(offset=self._update_offset)

            events: list[InboundEvent] = []
            if not updates:
                return events

            # Bump offset past the max update_id we saw.
            max_id = self._update_offset or 0
            for upd in updates:
                try:
                    update_id = int(upd.get("update_id"))
                except (TypeError, ValueError):
                    continue
                max_id = max(max_id, update_id + 1)

                msg = upd.get("message") or upd.get("edited_message")
                if not msg:
                    continue
                chat = msg.get("chat") or {}
                chat_id = chat.get("id")
                text = msg.get("text") or ""
                if chat_id is None or not text:
                    continue
                if allowed and int(chat_id) not in allowed:
                    logger.debug(
                        "Telegram: chat_id %s not in allowlist; ignoring",
                        chat_id,
                    )
                    continue

                # Repo resolution happens in process_event via its own
                # session; here we stash everything we need in ``raw``.
                with self._session() as db:
                    repo_id, task_text = self._resolve_repo_and_task(
                        db, text, default_repo
                    )

                title = task_text.splitlines()[0][:120] if task_text else text[:120]
                events.append(
                    InboundEvent(
                        source="telegram",
                        external_id=str(update_id),
                        title=title or "telegram-task",
                        body=task_text,
                        repository_id=repo_id,
                        raw={
                            "chat_id": int(chat_id),
                            "text": text,
                            "message_id": msg.get("message_id"),
                        },
                    )
                )
            self._update_offset = max_id
            return events

        return await asyncio.to_thread(_blocking)

    async def process_event(self, event: InboundEvent) -> None:
        chat_id = int(event.raw.get("chat_id", 0))

        def _blocking() -> tuple[int | None, str | None]:
            """Returns (swarm_id_or_none, bot_token_for_reply)."""
            with self._session() as db:
                token, _allowed, _default = self._load_config(db)

                # Dedup
                existing = db.get(
                    ProcessedEvent, (event.source, event.external_id)
                )
                if existing is not None:
                    return None, token

                if event.repository_id is None:
                    db.add(
                        ProcessedEvent(
                            source=event.source,
                            external_id=event.external_id,
                            processed_at=datetime.now(timezone.utc),
                            swarm_id=None,
                        )
                    )
                    logger.warning(
                        "Telegram event %s: no repository_id; marking processed",
                        event.external_id,
                    )
                    return None, token

                repo = db.get(Repository, event.repository_id)
                if repo is None:
                    db.add(
                        ProcessedEvent(
                            source=event.source,
                            external_id=event.external_id,
                            processed_at=datetime.now(timezone.utc),
                            swarm_id=None,
                        )
                    )
                    return None, token

                agents = (
                    db.query(Agent)
                    .filter(Agent.is_active.is_(True))
                    .order_by(Agent.id.asc())
                    .all()
                )
                if not agents:
                    db.add(
                        ProcessedEvent(
                            source=event.source,
                            external_id=event.external_id,
                            processed_at=datetime.now(timezone.utc),
                            swarm_id=None,
                        )
                    )
                    return None, token

                slug = _slugify(event.title)
                swarm_name = f"tg-{slug}-{event.external_id}"[:64]
                task_desc = event.body or event.title

                swarm = Swarm(
                    name=swarm_name,
                    repository_id=repo.id,
                    task_description=task_desc,
                    orchestrator_strategy="auto",
                    status="idle",
                    is_active=True,
                )
                db.add(swarm)
                db.flush()

                for pos, a in enumerate(agents):
                    db.add(
                        SwarmAgent(
                            swarm_id=swarm.id,
                            agent_id=a.id,
                            position=pos,
                        )
                    )
                db.add(
                    ProcessedEvent(
                        source=event.source,
                        external_id=event.external_id,
                        processed_at=datetime.now(timezone.utc),
                        swarm_id=swarm.id,
                    )
                )
                db.flush()
                return swarm.id, token

        swarm_id, token = await asyncio.to_thread(_blocking)
        if token and chat_id and swarm_id is not None:
            client = self._client_factory(token)
            client.send_message(
                chat_id,
                f"Syntexa: spawned swarm #{swarm_id} for your task.",
            )

        if swarm_id is None:
            return

        async def _run_and_reply() -> None:
            def _sync() -> Any:
                return self._run_swarm(swarm_id)

            try:
                result = await asyncio.to_thread(_sync)
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Telegram listener: run_swarm(%s) raised", swarm_id
                )
                if token and chat_id:
                    client = self._client_factory(token)
                    client.send_message(
                        chat_id,
                        f"Syntexa: swarm #{swarm_id} failed: {exc}",
                    )
                return
            if token and chat_id:
                client = self._client_factory(token)
                summary = _summarize_result(result, swarm_id)
                client.send_message(chat_id, summary)

        asyncio.create_task(_run_and_reply())


def _summarize_result(result: Any, swarm_id: int) -> str:
    """Best-effort Telegram reply body — handles dataclass / dict / str."""
    try:
        outputs = getattr(result, "agent_outputs", None)
        if outputs is None and isinstance(result, dict):
            outputs = result.get("agent_outputs")
        if not outputs:
            return f"Syntexa: swarm #{swarm_id} completed (no outputs)."
        chunks = []
        for aid, text in outputs.items():
            snippet = str(text)[:400]
            chunks.append(f"[{aid}] {snippet}")
        joined = "\n\n".join(chunks)
        return f"Syntexa: swarm #{swarm_id} done.\n\n{joined}"
    except Exception:  # noqa: BLE001
        return f"Syntexa: swarm #{swarm_id} finished."

"""ClickUp polling listener — auto-spawns swarms for tagged tasks.

On each poll we:

1. Load every active ``Repository`` with a ``clickup_list_id`` set.
2. For each repo, call ``ClickUpAdapter.list_tasks(trigger_tag)`` where
   ``trigger_tag`` comes from ``repo.clickup_trigger_tag`` (defaulting
   to ``syntexa-auto``). The adapter returns only tasks carrying that
   tag.
3. For each returned task, check ``ProcessedEvent`` — if we've seen
   the ClickUp task id before, skip. Otherwise emit an ``InboundEvent``.
4. ``process_event`` creates a fresh ``Swarm`` row wired to every
   ``is_active=True`` agent, writes a ``ProcessedEvent`` row, then
   fires ``run_swarm`` in a background asyncio task.

ClickUp credentials are sourced from ``ExternalCredential`` rows with
``service_type="clickup"``. One credential is assumed per deployment;
if multiple are active, the first by id wins.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from syntexa.adapters.clickup import ClickUpAdapter
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

DEFAULT_TRIGGER_TAG = "syntexa-auto"

#: Hook so tests can replace ``run_swarm`` with a stub without patching.
RunSwarmCallable = Callable[..., object]


def _slugify(value: str, *, max_len: int = 48) -> str:
    """Kebab-case slug good enough for a Swarm.name (unique index).

    We append a timestamp in the caller to guarantee uniqueness — this
    just cleans up the human-readable portion.
    """
    s = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not s:
        s = "task"
    return s[:max_len]


class ClickUpListener(Listener):
    """Watches ClickUp lists for tasks tagged ``syntexa-auto`` (or a
    per-repo override)."""

    name = "clickup"

    def __init__(
        self,
        *,
        poll_interval: float = 60.0,
        error_backoff: float = 10.0,
        max_backoff: float = 600.0,
        adapter_factory: Callable[[str, str], ClickUpAdapter] | None = None,
        run_swarm_impl: RunSwarmCallable | None = None,
        session_factory: Callable[[], Session] | None = None,
    ) -> None:
        """``adapter_factory`` and ``run_swarm_impl`` are test seams.

        Production: both ``None``. Tests pass fakes to sidestep network +
        the real orchestrator.

        ``session_factory`` returns a context-manager-like session. When
        ``None`` we use the module-level ``session_scope``.
        """
        super().__init__(
            poll_interval=poll_interval,
            error_backoff=error_backoff,
            max_backoff=max_backoff,
        )
        self._adapter_factory = adapter_factory or (
            lambda api_key, list_id: ClickUpAdapter(api_key, list_id)
        )
        if run_swarm_impl is None:
            # Imported lazily so test stubs don't pull in autogen.
            from syntexa.orchestrator.executor import run_swarm as _rs

            run_swarm_impl = _rs
        self._run_swarm = run_swarm_impl
        self._session_factory = session_factory

    # --- helpers ----------------------------------------------------------

    def _session(self):
        if self._session_factory is not None:
            return self._session_factory()
        return session_scope()

    def _get_api_key(self, db: Session) -> str | None:
        cred = (
            db.query(ExternalCredential)
            .filter_by(service_type="clickup", is_active=True)
            .order_by(ExternalCredential.id.asc())
            .first()
        )
        if cred is None:
            return None
        data = cred.get_credentials()
        return data.get("api_key")

    # --- Listener API -----------------------------------------------------

    async def poll_once(self) -> list[InboundEvent]:
        """Returns everything we saw this tick; dedup happens in
        ``process_event`` so a restart doesn't re-fire."""

        def _blocking() -> list[InboundEvent]:
            events: list[InboundEvent] = []
            with self._session() as db:
                api_key = self._get_api_key(db)
                if not api_key:
                    logger.debug(
                        "ClickUp listener: no api_key credential; skipping"
                    )
                    return []

                repos = (
                    db.query(Repository)
                    .filter(
                        Repository.is_active.is_(True),
                        Repository.clickup_list_id.isnot(None),
                    )
                    .all()
                )
                for repo in repos:
                    trigger_tag = (
                        repo.clickup_trigger_tag or DEFAULT_TRIGGER_TAG
                    )
                    try:
                        adapter = self._adapter_factory(
                            api_key, repo.clickup_list_id or ""
                        )
                        tasks = adapter.list_tasks(trigger_tag)
                    except Exception:  # noqa: BLE001
                        logger.exception(
                            "ClickUp listener: list_tasks failed for repo %s",
                            repo.id,
                        )
                        continue

                    for t in tasks:
                        events.append(
                            InboundEvent(
                                source="clickup",
                                external_id=str(t.id),
                                title=t.name,
                                body=t.description or "",
                                repository_id=repo.id,
                                raw={
                                    "status": t.status,
                                    "url": t.url,
                                    "tags": list(t.tags),
                                },
                            )
                        )
            return events

        return await asyncio.to_thread(_blocking)

    async def process_event(self, event: InboundEvent) -> None:
        if event.repository_id is None:
            logger.debug(
                "ClickUp event %s has no repository_id; skipping",
                event.external_id,
            )
            return

        def _blocking() -> int | None:
            """Returns the new swarm_id (or None) while holding one
            session. We do this in a thread so we don't block the loop
            on SQLite I/O."""
            with self._session() as db:
                # Dedup check
                existing = db.get(
                    ProcessedEvent, (event.source, event.external_id)
                )
                if existing is not None:
                    return None

                repo = db.get(Repository, event.repository_id)
                if repo is None:
                    logger.warning(
                        "Repository %s vanished between poll and process",
                        event.repository_id,
                    )
                    return None

                agents = (
                    db.query(Agent)
                    .filter(Agent.is_active.is_(True))
                    .order_by(Agent.id.asc())
                    .all()
                )
                if not agents:
                    # Record dedup anyway — no agents means no swarm.
                    db.add(
                        ProcessedEvent(
                            source=event.source,
                            external_id=event.external_id,
                            processed_at=datetime.now(timezone.utc),
                            swarm_id=None,
                        )
                    )
                    logger.warning(
                        "ClickUp event %s: no active agents; marking processed",
                        event.external_id,
                    )
                    return None

                # Build a unique swarm name: "clickup-<slug>-<external_id>"
                slug = _slugify(event.title)
                swarm_name = f"clickup-{slug}-{event.external_id}"[:64]
                task_desc = (
                    event.title
                    if not event.body
                    else f"{event.title}\n\n{event.body}"
                )

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
                return swarm.id

        swarm_id = await asyncio.to_thread(_blocking)
        if swarm_id is None:
            return

        logger.info(
            "ClickUp listener: spawned swarm %s for task %s",
            swarm_id,
            event.external_id,
        )

        # Fire-and-forget run — Phase 7 does NOT queue; it just hands off.
        def _run() -> None:
            try:
                self._run_swarm(swarm_id)
            except Exception:  # noqa: BLE001
                logger.exception(
                    "ClickUp listener: run_swarm(%s) raised", swarm_id
                )

        asyncio.create_task(asyncio.to_thread(_run))

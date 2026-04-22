"""Inbound event shape shared by all listeners.

A listener's ``poll_once`` returns a list of these; ``process_event``
consumes one at a time. Keeping the shape source-agnostic means the
swarm-creation code path is the same whether the trigger came from
ClickUp, Telegram, or a future Slack/webhook listener.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class InboundEvent:
    """A single trigger event picked up by a listener.

    - ``source``: which listener produced it (used as the dedup PK prefix)
    - ``external_id``: the upstream system's own id (ClickUp task id,
      Telegram update_id). Together with ``source`` this is the dedup key
      stored in ``processed_events``.
    - ``title`` / ``body``: free-form text used to build the swarm task
      description. For ClickUp: task name + description. For Telegram:
      message text (title is trimmed preview).
    - ``repository_id``: which repo the swarm should run against. If the
      listener can't figure it out, this is ``None`` and ``process_event``
      skips + logs.
    - ``raw``: the original payload, kept around for logging / debugging.
    """

    source: Literal["clickup", "telegram"]
    external_id: str
    title: str
    body: str
    repository_id: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

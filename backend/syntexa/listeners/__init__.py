"""H24 background listeners that spawn swarms on external triggers.

Public API:

- ``Listener``: ABC for a polling listener (implement ``poll_once`` +
  ``process_event``).
- ``InboundEvent``: the shape ``poll_once`` returns.
- ``ClickUpListener`` / ``TelegramListener``: concrete listeners.
- ``registry``: process-wide start/stop/status.

The FastAPI app does NOT auto-start listeners — control is via the
``/api/v1/listeners/*`` endpoints.
"""
from syntexa.listeners.base import Listener
from syntexa.listeners.clickup_listener import ClickUpListener
from syntexa.listeners.event import InboundEvent
from syntexa.listeners.telegram_listener import TelegramListener

__all__ = [
    "ClickUpListener",
    "InboundEvent",
    "Listener",
    "TelegramListener",
]

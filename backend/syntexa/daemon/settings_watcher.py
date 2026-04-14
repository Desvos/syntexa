"""Settings change notification system for daemon.

Uses a file-based trigger mechanism to notify the daemon that
settings have changed and should be reloaded.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Callable

from sqlalchemy.orm import Session

from syntexa.models import SystemSetting

logger = logging.getLogger(__name__)

# Default location for the trigger file (in the same directory as the database)
DEFAULT_TRIGGER_PATH = Path("./.syntexa_settings_changed")


class SettingsWatcher:
    """Watches for settings changes and notifies callbacks.

    Uses a file-based trigger mechanism:
    - API writes a trigger file when settings change
    - Daemon polls for this file and reloads settings
    - Trigger file is removed after successful reload
    """

    def __init__(self, trigger_path: Path | str | None = None) -> None:
        self.trigger_path = Path(trigger_path or DEFAULT_TRIGGER_PATH)
        self._callbacks: list[Callable[[], None]] = []
        self._lock = threading.Lock()
        self._last_check: float = 0
        self._check_interval: float = 5.0  # seconds between checks

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when settings change."""
        with self._lock:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[], None]) -> None:
        """Unregister a callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def trigger_reload(self) -> None:
        """Create the trigger file to signal settings change."""
        try:
            self.trigger_path.touch()
            logger.debug("Settings reload triggered")
        except OSError as e:
            logger.error("Failed to create settings trigger file: %s", e)

    def check_and_reload(self, db: Session) -> bool:
        """Check if settings have changed and reload if necessary.

        Returns True if settings were reloaded.
        """
        current_time = time.time()

        # Rate limit checks
        if current_time - self._last_check < self._check_interval:
            return False

        self._last_check = current_time

        if not self.trigger_path.exists():
            return False

        # Trigger file exists - reload settings
        logger.info("Settings change detected, reloading...")

        try:
            # Remove trigger file
            self.trigger_path.unlink()

            # Call all registered callbacks
            with self._lock:
                callbacks = self._callbacks.copy()

            for callback in callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error("Error in settings reload callback: %s", e)

            logger.info("Settings reloaded successfully")
            return True

        except OSError as e:
            logger.error("Failed to process settings reload: %s", e)
            return False

    def get_current_settings(self, db: Session) -> dict[str, any]:
        """Get all current system settings from database."""
        settings = {}
        for setting in db.query(SystemSetting).all():
            settings[setting.key] = setting.get_value()
        return settings


# Global watcher instance
_global_watcher: SettingsWatcher | None = None
_global_lock = threading.Lock()


def get_watcher(trigger_path: Path | str | None = None) -> SettingsWatcher:
    """Get or create the global settings watcher instance."""
    global _global_watcher

    with _global_lock:
        if _global_watcher is None:
            _global_watcher = SettingsWatcher(trigger_path)
        return _global_watcher


def trigger_daemon_reload() -> None:
    """Signal the daemon to reload settings.

    This should be called by the API after updating settings.
    """
    watcher = get_watcher()
    watcher.trigger_reload()

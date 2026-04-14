"""Concurrency control (FR-11).

Wraps a ThreadPoolExecutor with an active-task set so the poller can
- skip tasks that are already running (dedup), and
- stop submitting when the pool is saturated (queue stays on the PM side).
"""
from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor

logger = logging.getLogger(__name__)


class SwarmExecutor:
    def __init__(self, max_concurrent: int) -> None:
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be >= 1")
        self._max = max_concurrent
        self._pool = ThreadPoolExecutor(
            max_workers=max_concurrent,
            thread_name_prefix="syntexa-swarm",
        )
        self._active: set[str] = set()
        self._lock = threading.Lock()

    @property
    def max_concurrent(self) -> int:
        return self._max

    def active_count(self) -> int:
        with self._lock:
            return len(self._active)

    def is_full(self) -> bool:
        return self.active_count() >= self._max

    def is_active(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._active

    def submit(self, task_id: str, fn: Callable[[], None]) -> Future | None:
        """Submit a task job. Returns None if the task is already active or
        the pool is saturated — the poller interprets None as "try again
        next cycle"."""
        with self._lock:
            if task_id in self._active:
                logger.debug("Task %s already active; skipping", task_id)
                return None
            if len(self._active) >= self._max:
                logger.info(
                    "Executor saturated (%d/%d); deferring task %s",
                    len(self._active),
                    self._max,
                    task_id,
                )
                return None
            self._active.add(task_id)

        future = self._pool.submit(self._wrap, task_id, fn)
        return future

    def _wrap(self, task_id: str, fn: Callable[[], None]) -> None:
        try:
            fn()
        except Exception:
            logger.exception("Swarm job for task %s raised", task_id)
        finally:
            with self._lock:
                self._active.discard(task_id)

    def shutdown(self, wait: bool = True) -> None:
        self._pool.shutdown(wait=wait)

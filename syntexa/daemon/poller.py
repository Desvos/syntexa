"""Task polling loop (FR-1).

Polls the project-management adapter for tagged tasks at `poll_interval`.
For each task not already active, builds a swarm job and submits it to
the executor. Adapter errors are logged and do not interrupt the loop
(FR-1 acceptance: polling failures do not disrupt running swarms).
"""
from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

from syntexa.adapters.base import ProjectManagementAdapter, TaskRef
from syntexa.daemon.executor import SwarmExecutor

logger = logging.getLogger(__name__)

# Factory: given a task, return a zero-arg callable that runs the swarm.
SwarmJobFactory = Callable[[TaskRef], Callable[[], None]]


class Poller:
    def __init__(
        self,
        pm: ProjectManagementAdapter,
        executor: SwarmExecutor,
        job_factory: SwarmJobFactory,
        *,
        poll_interval: int,
        trigger_tag: str,
    ) -> None:
        self._pm = pm
        self._executor = executor
        self._job_factory = job_factory
        self._poll_interval = poll_interval
        self._trigger_tag = trigger_tag
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def poll_once(self) -> int:
        """Run a single polling cycle. Returns the number of jobs submitted."""
        try:
            tasks = self._pm.list_tasks(self._trigger_tag)
        except Exception:
            logger.exception("Polling adapter call failed")
            return 0

        submitted = 0
        for task in tasks:
            if self._executor.is_full():
                break
            if self._executor.is_active(task.id):
                continue
            job = self._job_factory(task)
            if self._executor.submit(task.id, job) is not None:
                submitted += 1
        return submitted

    def run_forever(self) -> None:
        logger.info(
            "Poller started (interval=%ss, tag=%s)",
            self._poll_interval,
            self._trigger_tag,
        )
        while not self._stop_event.is_set():
            started = time.monotonic()
            self.poll_once()
            elapsed = time.monotonic() - started
            # `wait` returns True if stop() was called — exits promptly on shutdown.
            if self._stop_event.wait(max(0.0, self._poll_interval - elapsed)):
                break
        logger.info("Poller stopped")

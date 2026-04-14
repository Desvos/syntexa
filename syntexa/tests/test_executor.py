"""T033 — concurrency test for SwarmExecutor (FR-11)."""
from __future__ import annotations

import threading
import time

from syntexa.daemon.executor import SwarmExecutor


def test_enforces_max_concurrent() -> None:
    executor = SwarmExecutor(max_concurrent=2)
    gate = threading.Event()
    running = threading.Semaphore(0)

    def job() -> None:
        running.release()
        gate.wait(timeout=2.0)

    f1 = executor.submit("t1", job)
    f2 = executor.submit("t2", job)
    # Wait until both jobs are actually running inside the pool.
    assert running.acquire(timeout=1.0)
    assert running.acquire(timeout=1.0)

    # Pool is full → third submit must return None without blocking.
    assert executor.submit("t3", job) is None
    assert executor.is_full()
    assert executor.active_count() == 2

    gate.set()
    f1.result(timeout=2.0)
    f2.result(timeout=2.0)

    # Active set cleared after completion.
    assert executor.active_count() == 0

    # A new slot is available; same task_id can now submit again.
    f3 = executor.submit("t1", lambda: None)
    assert f3 is not None
    f3.result(timeout=2.0)

    executor.shutdown()


def test_dedup_rejects_already_active_task() -> None:
    executor = SwarmExecutor(max_concurrent=3)
    gate = threading.Event()

    def job() -> None:
        gate.wait(timeout=2.0)

    assert executor.submit("same", job) is not None
    # Same task_id while active → None.
    assert executor.submit("same", job) is None
    gate.set()
    time.sleep(0.05)  # let the wrapper clean up the active set
    executor.shutdown()


def test_exception_in_job_does_not_poison_executor() -> None:
    executor = SwarmExecutor(max_concurrent=1)

    def boom() -> None:
        raise RuntimeError("kaboom")

    f = executor.submit("t1", boom)
    assert f is not None
    f.result(timeout=1.0)  # _wrap swallows the exception
    assert executor.active_count() == 0

    # Next submit still works.
    f2 = executor.submit("t1", lambda: None)
    assert f2 is not None
    f2.result(timeout=1.0)
    executor.shutdown()

"""Unit tests for the task-type classifier (FR-2)."""
from __future__ import annotations

import pytest

from syntexa.adapters.base import TaskRef
from syntexa.daemon.classifier import classify


def _task(name: str, tags: tuple[str, ...] = ()) -> TaskRef:
    return TaskRef(id="1", name=name, description="", tags=tags, status="open")


@pytest.mark.parametrize(
    "name,tags,expected",
    [
        ("Add login page", (), "feature"),
        ("Fix crash on logout", (), "fix"),
        ("refactor auth module", (), "refactor"),
        ("CVE-2025-1234 security patch", (), "security"),
        ("bump deps", (), "chore"),
        ("whatever", ("security",), "security"),
        ("whatever", ("fix",), "fix"),
        # Tag beats title.
        ("fix the thing", ("feature",), "feature"),
    ],
)
def test_classify(name: str, tags: tuple[str, ...], expected: str) -> None:
    assert classify(_task(name, tags)) == expected

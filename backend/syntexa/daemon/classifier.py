"""Task-type detection (FR-2).

Classifies a TaskRef into one of: feature (default), fix, refactor, security, chore.
Keyword match on tags first (cheaper, more deliberate), then on the task title.
"""
from __future__ import annotations

from syntexa.adapters.base import TaskRef

# Ordered: higher specificity wins in ties.
TASK_TYPE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("security", ("security", "cve", "vuln", "audit")),
    ("fix", ("fix", "bug", "hotfix", "patch")),
    ("refactor", ("refactor", "cleanup", "rework")),
    ("chore", ("chore", "deps", "dependency", "docs")),
    ("feature", ("feature", "feat")),
)

DEFAULT_TASK_TYPE = "feature"


def classify(task: TaskRef) -> str:
    lowered_tags = {t.lower() for t in task.tags}
    lowered_title = task.name.lower()

    for task_type, keywords in TASK_TYPE_KEYWORDS:
        if lowered_tags.intersection(keywords):
            return task_type

    for task_type, keywords in TASK_TYPE_KEYWORDS:
        if any(kw in lowered_title for kw in keywords):
            return task_type

    return DEFAULT_TASK_TYPE

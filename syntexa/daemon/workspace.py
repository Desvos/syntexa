"""Isolated workspace per swarm (FR-5).

A workspace is a branch in the local clone at `settings.repo_path`. Only
one swarm may hold a given branch; the executor enforces uniqueness by
task_id, and branch names are derived from task_id.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from syntexa.adapters.base import RepositoryAdapter

logger = logging.getLogger(__name__)

_SANITIZE_RE = re.compile(r"[^a-z0-9]+")


def branch_name_for(task_id: str, task_name: str, *, prefix: str = "syntexa") -> str:
    """Generate a git-safe branch name. Deterministic per task_id so retries
    reuse the same branch."""
    slug_source = task_name or task_id
    slug = _SANITIZE_RE.sub("-", slug_source.lower()).strip("-")[:40] or "task"
    return f"{prefix}/{task_id}-{slug}"


class Workspace:
    """Manages branch lifecycle for one task.

    `prepare()` creates/checks out the branch. `finalize()` is a no-op on
    the filesystem — push and PR creation happen in the delivery pipeline.
    Failure recovery in `cleanup()` returns the working copy to base_branch
    so the next swarm starts from a clean tree.
    """

    def __init__(
        self,
        repo: RepositoryAdapter,
        repo_path: Path,
        base_branch: str,
    ) -> None:
        self._repo = repo
        self._repo_path = repo_path
        self._base_branch = base_branch

    @property
    def path(self) -> Path:
        return self._repo_path

    def prepare(self, branch: str) -> Path:
        self._repo.create_branch(branch, self._base_branch)
        logger.info("Prepared workspace at %s on branch %s", self._repo_path, branch)
        return self._repo_path

    def cleanup(self, branch: str) -> None:
        """Best-effort return to base_branch. We do NOT delete the branch —
        a reviewer may still want to inspect it even on failure."""
        try:
            self._repo.create_branch(self._base_branch, self._base_branch)
        except Exception:
            logger.exception("Workspace cleanup failed for branch %s", branch)

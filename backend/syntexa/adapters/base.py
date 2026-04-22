"""Abstract base classes for pluggable project-management and repository adapters.

The daemon depends on these interfaces, not on concrete vendors (ClickUp, GitHub, ...).
Concrete implementations live in sibling modules (e.g. `clickup.py`, `github.py`).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

TaskStatus = Literal["open", "in_progress", "blocked", "done", "error"]


@dataclass(frozen=True)
class TaskRef:
    """Normalized task representation returned by project-management adapters."""

    id: str
    name: str
    description: str
    tags: tuple[str, ...]
    status: str
    url: str | None = None


class ProjectManagementAdapter(ABC):
    """Contract for project-management systems (ClickUp, Jira, Linear, ...)."""

    @abstractmethod
    def list_tasks(self, tag: str) -> list[TaskRef]:
        """Return tasks matching a trigger tag. Implementations must not raise
        for transient network errors — log and return an empty list instead."""

    @abstractmethod
    def update_status(self, task_id: str, status: TaskStatus) -> None:
        """Move a task to the given normalized status."""

    @abstractmethod
    def add_comment(self, task_id: str, body: str) -> None:
        """Attach a free-form comment to a task (used for progress updates)."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the backing service is reachable with valid credentials."""


class NoOpProjectManagementAdapter(ProjectManagementAdapter):
    """No-op adapter used when no project management integration is configured.

    All operations succeed silently and return empty results.
    """

    def list_tasks(self, tag: str) -> list[TaskRef]:
        return []

    def update_status(self, task_id: str, status: TaskStatus) -> None:
        pass

    def add_comment(self, task_id: str, body: str) -> None:
        pass

    def health_check(self) -> bool:
        return True


@dataclass(frozen=True)
class PullRequestRef:
    number: int
    url: str
    branch: str
    title: str


class RepositoryAdapter(ABC):
    """Contract for source-control hosts (GitHub, GitLab, Gitea, ...)."""

    @abstractmethod
    def create_branch(self, name: str, base: str) -> None:
        """Create `name` off of `base`. Must be idempotent if the branch already exists."""

    @abstractmethod
    def commit(self, branch: str, message: str, paths: list[str]) -> str:
        """Stage `paths`, commit with `message` on `branch`, return the commit SHA."""

    @abstractmethod
    def push(self, branch: str) -> None:
        """Push `branch` to the remote."""

    @abstractmethod
    def create_pr(
        self,
        head: str,
        base: str,
        title: str,
        body: str,
    ) -> PullRequestRef:
        """Open a pull request from `head` into `base`."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the repository host is reachable with valid credentials."""


class LocalRepositoryAdapter(RepositoryAdapter):
    """Local Git adapter that only commits to local branches without pushing.

    Used when no remote repository integration is configured.
    """

    from pathlib import Path

    def __init__(self, repo_path: Path) -> None:
        self._path = repo_path
        import subprocess
        self._subprocess = subprocess

        # Verify git repo exists
        result = self._subprocess.run(
            ["git", "-C", str(self._path), "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Not a git repository: {self._path}")

    def _git(self, args: list[str]) -> None:
        result = self._subprocess.run(
            ["git", "-C", str(self._path)] + args,
            capture_output=True,
            text=True,
            check=True,
        )

    def create_branch(self, name: str, base: str) -> None:
        self._git(["checkout", "-B", name, base])

    def commit(self, branch: str, message: str, paths: list[str]) -> str:
        self._git(["checkout", branch])
        self._git(["add"] + paths)
        self._git(["commit", "-m", message])
        result = self._subprocess.run(
            ["git", "-C", str(self._path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def push(self, branch: str) -> None:
        pass  # No-op for local-only adapter

    def create_pr(
        self,
        head: str,
        base: str,
        title: str,
        body: str,
    ) -> PullRequestRef:
        # Return a fake PR ref with local branch info
        return PullRequestRef(
            number=0,
            url=f"file://{self._path}#{head}",
            branch=head,
            title=title,
        )

    def health_check(self) -> bool:
        result = self._subprocess.run(
            ["git", "-C", str(self._path), "status"],
            capture_output=True,
        )
        return result.returncode == 0

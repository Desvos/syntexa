"""Pluggable adapters for external services."""
from syntexa.adapters.base import (
    ProjectManagementAdapter,
    PullRequestRef,
    RepositoryAdapter,
    TaskRef,
    TaskStatus,
)

__all__ = [
    "ProjectManagementAdapter",
    "PullRequestRef",
    "RepositoryAdapter",
    "TaskRef",
    "TaskStatus",
]

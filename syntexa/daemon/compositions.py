"""Default swarm compositions per task type (FR-3, FR-8).

Maps each task type to an ordered list of role names. The first role is
the swarm's entry point; the order defines the default handoff chain,
though agents may hand off out of order within their allowed targets.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompositionConfig:
    task_type: str
    roles: tuple[str, ...]
    max_rounds: int = 60


DEFAULT_COMPOSITIONS: tuple[CompositionConfig, ...] = (
    # Greenfield work: full pipeline.
    CompositionConfig("feature", ("planner", "coder", "tester", "reviewer")),
    # Bug fix: skip planner, coder starts from the diagnosis in the task body.
    CompositionConfig("fix", ("coder", "tester", "reviewer")),
    # Refactor: planner first (critical for scope), two coders allowed for parallel work.
    CompositionConfig("refactor", ("planner", "coder", "coder", "tester", "reviewer"), 80),
    # Security: planner for threat analysis, tighter max_rounds to keep focus.
    CompositionConfig("security", ("planner", "coder", "tester", "reviewer"), 40),
    # Chores (deps, docs): coder + reviewer only.
    CompositionConfig("chore", ("coder", "reviewer"), 30),
)


def get_default_composition(task_type: str) -> CompositionConfig | None:
    for comp in DEFAULT_COMPOSITIONS:
        if comp.task_type == task_type:
            return comp
    return None

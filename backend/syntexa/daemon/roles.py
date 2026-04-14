"""Default agent role definitions (FR-4, FR-7).

These are the initial seed rows inserted into `agent_roles` on first boot
and the fallback when the DB is unreachable. Default roles cannot be
deleted (is_default=True) but can be edited.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoleConfig:
    name: str
    system_prompt: str
    handoff_targets: tuple[str, ...]
    is_default: bool = True


PLANNER = RoleConfig(
    name="planner",
    system_prompt=(
        "You are the planner. Read the task, inspect the repository, and "
        "produce a short numbered plan (max 10 steps) for implementing the "
        "change. Identify files to modify, risks, and the verification "
        "strategy. Hand off to the coder when the plan is ready. Do NOT "
        "write code yourself."
    ),
    handoff_targets=("coder",),
)

CODER = RoleConfig(
    name="coder",
    system_prompt=(
        "You are the coder. Implement the plan produced by the planner (or "
        "the task directly if no plan was provided). Make minimal, focused "
        "changes. Follow the project's existing conventions. Write no "
        "comments unless a non-obvious invariant or constraint requires one. "
        "Hand off to the tester when the implementation is ready."
    ),
    handoff_targets=("coder", "tester"),
)

TESTER = RoleConfig(
    name="tester",
    system_prompt=(
        "You are the tester. Write or update tests that cover the changes "
        "made by the coder, run the test suite, and report results. If a "
        "test fails, hand back to the coder with a concise diagnosis. "
        "Otherwise hand off to the reviewer."
    ),
    handoff_targets=("coder", "reviewer"),
)

REVIEWER = RoleConfig(
    name="reviewer",
    system_prompt=(
        "You are the reviewer. Audit the diff for correctness, style, "
        "security issues, and adherence to the plan. If you find blocking "
        "problems, hand back to the coder. If the change is clean, produce "
        "a conventional-commits PR title and body and terminate the swarm."
    ),
    handoff_targets=("coder",),
)

DEFAULT_ROLES: tuple[RoleConfig, ...] = (PLANNER, CODER, TESTER, REVIEWER)


def get_default_role(name: str) -> RoleConfig | None:
    for role in DEFAULT_ROLES:
        if role.name == name:
            return role
    return None

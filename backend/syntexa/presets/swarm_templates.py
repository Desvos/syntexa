"""Built-in Swarm blueprints.

Each template names a set of agent presets (by ``name`` from
``BUILTIN_AGENT_PRESETS``) and picks an orchestrator strategy.
``apply_preset("swarm_template", ...)`` seeds any missing agents from the
agent preset library before creating the Swarm row.
"""
from __future__ import annotations

from typing import Any

BUILTIN_SWARM_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "quick-fix",
        "description": "Single coder fixes a small bug.",
        "agent_names": ["coder"],
        "orchestrator_strategy": "sequential",
    },
    {
        "name": "feature-dev",
        "description": "Planner -> Coder -> Reviewer -> Tester.",
        "agent_names": ["planner", "coder", "reviewer", "tester"],
        "orchestrator_strategy": "sequential",
    },
    {
        "name": "review-only",
        "description": "Reviewer + Tester in parallel.",
        "agent_names": ["reviewer", "tester"],
        "orchestrator_strategy": "parallel",
    },
    {
        "name": "auto",
        "description": "Planner, Coder, Reviewer — orchestrator decides.",
        "agent_names": ["planner", "coder", "reviewer"],
        "orchestrator_strategy": "auto",
    },
]

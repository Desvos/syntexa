"""Orchestration layer: takes a Swarm and decides how to run its agents.

The orchestrator is the meta-agent that sits above a Swarm's agents. It
picks between three strategies:

- ``parallel``  — fan out to every agent concurrently, merge outputs
- ``sequential`` — run agents in a fixed order, each sees prior outputs
- ``auto``     — ask an LLM meta-agent to pick one of the above

The public API is intentionally small: build a Swarm + agents, then call
``run_swarm(swarm_id)``. The /swarms/{id}/run HTTP endpoint is a thin
wrapper around it.
"""
from syntexa.orchestrator.decision import (
    OrchestratorDecision,
    decide_strategy,
)
from syntexa.orchestrator.executor import (
    Orchestrator,
    OrchestratorResult,
    run_swarm,
)

__all__ = [
    "Orchestrator",
    "OrchestratorDecision",
    "OrchestratorResult",
    "decide_strategy",
    "run_swarm",
]

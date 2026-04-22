"""Run a Swarm: build AG2 agents, dispatch parallel/sequential, collect outputs.

This module is the bridge between a stored ``Swarm`` row and a concrete
AG2 multi-agent invocation. It:

1. Loads the swarm + its agents + their providers
2. Calls ``decide_strategy`` to pick parallel vs sequential
3. Spins up one ``ConversableAgent`` per stored agent using each agent's
   own LLMProvider (agents can heterogeneously mix providers in one swarm)
4. Either ``asyncio.gather``s them (parallel) or walks them in order
   feeding prior outputs forward (sequential)
5. Writes ``swarm.status`` transitions idle→running→completed|failed

The AG2 call is injected via ``agent_runner`` so the test suite can
avoid hitting real LLMs; the default runner delegates to AG2's sync
``generate_reply`` wrapped in ``asyncio.to_thread``.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from sqlalchemy.orm import Session

from syntexa.llm.provider_config import build_llm_config
from syntexa.models import Agent, LLMProvider, Swarm, SwarmAgent
from syntexa.models.database import session_scope
from syntexa.orchestrator.decision import (
    OrchestratorDecision,
    decide_strategy,
)


AgentRunner = Callable[[Agent, LLMProvider, str], Awaitable[str]]
"""Signature for running a single agent against a prompt.

Tests stub this to capture what each agent was sent and return canned
replies. The production default spins up a ``ConversableAgent`` with the
right llm_config and calls ``generate_reply``.
"""


@dataclass
class OrchestratorResult:
    """Outcome of one swarm run.

    ``agent_outputs`` maps agent_id -> raw assistant text. For a failed
    run it contains whatever partial results landed before the error.
    """

    swarm_id: int
    strategy_used: str
    order: list[int] | None
    agent_outputs: dict[int, str] = field(default_factory=dict)
    success: bool = False
    error: str | None = None


class SwarmNotFoundError(Exception):
    """Raised by ``run_swarm`` when the swarm_id doesn't exist.

    The API layer translates this into a 404; keep it a dedicated type
    so callers can distinguish "bad ID" from "run blew up mid-flight".
    """


class SwarmAlreadyRunningError(Exception):
    """Raised when a swarm is re-entered while still marked ``running``.

    The API layer maps it to 409. We check BEFORE flipping to "running"
    so a stale-status row is self-healing once the old run is reaped.
    """


async def _default_agent_runner(
    agent: Agent, provider: LLMProvider, prompt: str
) -> str:
    """Real AG2 path: one-shot ``ConversableAgent.generate_reply``.

    Wrapped in ``asyncio.to_thread`` because ``generate_reply`` is
    synchronous in ag2 0.11 — using ``a_generate_reply`` would also work
    but keeping it on a thread avoids sharing one event loop across a
    provider's SDK (some SDKs spin up their own loops, which poisons
    ``asyncio.gather``).
    """
    from autogen import ConversableAgent

    llm_config = build_llm_config(provider, model=agent.model)
    conv = ConversableAgent(
        name=agent.name,
        system_message=agent.system_prompt,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    def _call() -> str:
        reply = conv.generate_reply(
            messages=[{"role": "user", "content": prompt}]
        )
        if isinstance(reply, dict):
            return str(reply.get("content", "") or "")
        return str(reply or "")

    return await asyncio.to_thread(_call)


def _load_swarm_bundle(
    session: Session, swarm_id: int
) -> tuple[Swarm, list[Agent], dict[int, LLMProvider]]:
    """Fetch swarm + its agents (in position order) + their providers.

    Returns ``(swarm, agents, providers_by_id)`` where ``providers_by_id``
    is keyed by provider_id so the caller can look up the right
    LLMProvider for each agent without a second query per agent.
    """
    swarm = session.get(Swarm, swarm_id)
    if swarm is None:
        raise SwarmNotFoundError(f"Swarm id={swarm_id} not found")

    rows = (
        session.query(Agent, SwarmAgent.position)
        .join(SwarmAgent, SwarmAgent.agent_id == Agent.id)
        .filter(SwarmAgent.swarm_id == swarm_id)
        .order_by(SwarmAgent.position.asc(), Agent.id.asc())
        .all()
    )
    agents = [a for a, _pos in rows]

    provider_ids = {a.provider_id for a in agents}
    providers: dict[int, LLMProvider] = {}
    if provider_ids:
        for prov in (
            session.query(LLMProvider)
            .filter(LLMProvider.id.in_(provider_ids))
            .all()
        ):
            providers[prov.id] = prov
    return swarm, agents, providers


def _pick_meta_provider(
    session: Session,
    agents: list[Agent],
    providers_by_id: dict[int, LLMProvider],
    meta_provider_id: int | None,
) -> LLMProvider:
    """Decide which provider hosts the meta-agent.

    Explicit ``meta_provider_id`` wins. Otherwise we fall back to the
    first active agent's provider — simplest sane default, and it means
    the meta-agent inherits whatever credentials the user already wired
    up for real agents.
    """
    if meta_provider_id is not None:
        prov = session.get(LLMProvider, meta_provider_id)
        if prov is None:
            raise ValueError(
                f"meta_provider_id={meta_provider_id} does not exist"
            )
        return prov
    for a in agents:
        if a.is_active and a.provider_id in providers_by_id:
            return providers_by_id[a.provider_id]
    # Nothing active — take whatever we have. decide_strategy will
    # short-circuit on "parallel"/"sequential" before it ever touches
    # the meta-provider, so this is only bad for true "auto" + no
    # active agents, which is a degenerate config anyway.
    for prov in providers_by_id.values():
        return prov
    raise ValueError("Swarm has no agents to derive a meta-provider from")


async def _run_parallel(
    agents_in_run: list[Agent],
    providers_by_id: dict[int, LLMProvider],
    task: str,
    runner: AgentRunner,
) -> dict[int, str]:
    """Dispatch every agent concurrently with the same task prompt."""
    coros = [
        runner(a, providers_by_id[a.provider_id], task) for a in agents_in_run
    ]
    results = await asyncio.gather(*coros)
    return {a.id: out for a, out in zip(agents_in_run, results)}


async def _run_sequential(
    agents_in_run: list[Agent],
    providers_by_id: dict[int, LLMProvider],
    task: str,
    runner: AgentRunner,
) -> dict[int, str]:
    """Walk agents in order; each prompt includes prior outputs as context.

    The prompt for agent N is ``task`` plus a "Previous agent outputs:"
    block containing every prior agent's name + reply. Keeps the
    hand-off simple and framework-agnostic — AG2's own group-chat could
    replace this later without changing the external contract.
    """
    outputs: dict[int, str] = {}
    for agent in agents_in_run:
        if outputs:
            prior_block = "\n\n".join(
                f"[{aid}] {text}" for aid, text in outputs.items()
            )
            prompt = (
                f"{task}\n\nPrevious agent outputs:\n{prior_block}"
            )
        else:
            prompt = task
        reply = await runner(
            agent, providers_by_id[agent.provider_id], prompt
        )
        outputs[agent.id] = reply
    return outputs


def _order_agents(
    agents: list[Agent], decision: OrchestratorDecision
) -> list[Agent]:
    """Realize an OrchestratorDecision.order into the actual agent list."""
    if decision.order is None:
        return list(agents)
    by_id = {a.id: a for a in agents}
    return [by_id[aid] for aid in decision.order if aid in by_id]


def run_swarm(
    swarm_id: int,
    task_override: str | None = None,
    *,
    meta_provider_id: int | None = None,
    session: Session | None = None,
    agent_runner: AgentRunner | None = None,
    decision_llm_caller=None,
) -> OrchestratorResult:
    """Run a swarm end-to-end and return the aggregated result.

    Synchronous entry point — internally the agent dispatch is async, but
    we drive it with ``asyncio.run`` so HTTP handlers (sync) and Phase 7
    listeners alike can call this without worrying about event-loop
    plumbing.

    ``agent_runner`` / ``decision_llm_caller`` are test hooks; leaving
    them ``None`` picks the real AG2 path.
    """
    owns_session = session is None
    if owns_session:
        ctx = session_scope()
        session = ctx.__enter__()

    swarm_id_for_result = swarm_id
    try:
        swarm, agents, providers_by_id = _load_swarm_bundle(session, swarm_id)

        if swarm.status == "running":
            raise SwarmAlreadyRunningError(
                f"Swarm id={swarm_id} is already running"
            )

        task = task_override if task_override is not None else (
            swarm.task_description or ""
        )

        # Resolve meta-provider BEFORE flipping status so we can bail out
        # without leaving the row in "running" if the config is broken.
        meta_provider = _pick_meta_provider(
            session, agents, providers_by_id, meta_provider_id
        )

        decision = decide_strategy(
            swarm, agents, meta_provider, llm_caller=decision_llm_caller
        )
        agents_in_run = _order_agents(agents, decision)

        swarm.status = "running"
        session.flush()
        if owns_session:
            session.commit()

        runner = agent_runner or _default_agent_runner
        try:
            if decision.strategy == "parallel":
                outputs = asyncio.run(
                    _run_parallel(
                        agents_in_run, providers_by_id, task, runner
                    )
                )
            else:
                outputs = asyncio.run(
                    _run_sequential(
                        agents_in_run, providers_by_id, task, runner
                    )
                )
        except Exception as exc:
            swarm.status = "failed"
            session.flush()
            if owns_session:
                session.commit()
            return OrchestratorResult(
                swarm_id=swarm.id,
                strategy_used=decision.strategy,
                order=decision.order,
                agent_outputs={},
                success=False,
                error=str(exc),
            )

        swarm.status = "completed"
        session.flush()
        if owns_session:
            session.commit()
        return OrchestratorResult(
            swarm_id=swarm.id,
            strategy_used=decision.strategy,
            order=decision.order,
            agent_outputs=outputs,
            success=True,
            error=None,
        )
    except SwarmNotFoundError:
        # Don't swallow — the API wants a 404, which means this has to
        # propagate up rather than becoming an OrchestratorResult.
        raise
    except SwarmAlreadyRunningError:
        raise
    except Exception as exc:
        # Any other unhandled path (DB glitch, bad meta-provider, ...)
        # gets surfaced as a failed result so callers always have
        # something to serialize. We try to record "failed" on the row
        # too, but we ignore errors during that write — the primary
        # failure is the more interesting one.
        try:
            row = session.get(Swarm, swarm_id)
            if row is not None and row.status == "running":
                row.status = "failed"
                session.flush()
                if owns_session:
                    session.commit()
        except Exception:
            pass
        return OrchestratorResult(
            swarm_id=swarm_id_for_result,
            strategy_used="unknown",
            order=None,
            agent_outputs={},
            success=False,
            error=str(exc),
        )
    finally:
        if owns_session:
            try:
                ctx.__exit__(None, None, None)
            except Exception:
                pass


class Orchestrator:
    """Thin OO wrapper for callers that prefer an object-shaped API.

    The module-level ``run_swarm`` is still the canonical entry point —
    this class just gives Phase 7 listeners a handle they can hold onto
    (e.g. for DI / swapping runners in tests).
    """

    def __init__(
        self,
        *,
        agent_runner: AgentRunner | None = None,
        decision_llm_caller=None,
    ) -> None:
        self.agent_runner = agent_runner
        self.decision_llm_caller = decision_llm_caller

    def run(
        self,
        swarm_id: int,
        task_override: str | None = None,
        *,
        meta_provider_id: int | None = None,
        session: Session | None = None,
    ) -> OrchestratorResult:
        return run_swarm(
            swarm_id,
            task_override,
            meta_provider_id=meta_provider_id,
            session=session,
            agent_runner=self.agent_runner,
            decision_llm_caller=self.decision_llm_caller,
        )

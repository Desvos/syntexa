"""Meta-agent strategy picker for a Swarm.

Given a Swarm row + its bound Agents + a provider to host the meta-agent,
decide whether the agents should run in parallel or sequential (and, if
sequential, in what order).

User overrides ("parallel" / "sequential") short-circuit the LLM call —
the meta-agent is only consulted when swarm.orchestrator_strategy is
"auto". For sequential overrides we also resolve the final order here so
the executor doesn't have to duplicate the "manual_agent_order first, else
SwarmAgent.position" fallback logic.

The LLM call is injected via ``llm_caller`` so tests can stub it out
cheaply — hitting real providers in a unit test would be both slow and
flaky.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Literal

from syntexa.llm.provider_config import build_llm_config
from syntexa.models import Agent, LLMProvider, Swarm


LLMCaller = Callable[[dict, str], str]
"""Signature for the injectable LLM adapter used by the meta-agent.

Arguments are ``(llm_config, prompt)`` where ``llm_config`` is the dict
produced by :func:`syntexa.llm.provider_config.build_llm_config`. Must
return the raw assistant text (we parse JSON out of it)."""


@dataclass
class OrchestratorDecision:
    """What the orchestrator decided to do for a swarm run.

    ``order`` is a list of agent IDs in execution order when
    ``strategy == "sequential"``; ``None`` for parallel runs (no order
    meaningful).
    """

    strategy: Literal["parallel", "sequential"]
    order: list[int] | None
    reasoning: str


def _position_order(swarm_id: int, agents: list[Agent]) -> list[int]:
    """Fallback: agent IDs in the order the caller handed them to us.

    The executor loads agents via the SwarmAgent join already sorted by
    ``position`` ASC (see :func:`syntexa.api.routes.swarms._agents_for_swarm`),
    so ``[a.id for a in agents]`` IS the position order. We accept that
    invariant rather than re-query the DB.
    """
    return [a.id for a in agents]


def _build_meta_prompt(swarm: Swarm, agents: list[Agent]) -> str:
    """Compose the JSON-returning prompt we feed the meta-agent."""
    agent_lines = "\n".join(
        f"- id={a.id} name={a.name}: {a.system_prompt}" for a in agents
    )
    task = swarm.task_description or "(no task description provided)"
    return (
        "You are an orchestrator. Decide how to run a group of agents.\n\n"
        f"Task: {task}\n\n"
        f"Agents:\n{agent_lines}\n\n"
        "Should they run in parallel (fully independent, outputs merged) "
        "or sequential (each building on the prior one)? If sequential, "
        "also pick the order.\n\n"
        'Reply with ONLY a JSON object, no prose: '
        '{"strategy":"parallel|sequential","order":[agent_ids_in_order_or_empty_list],'
        '"reasoning":"one short sentence"}'
    )


def _default_llm_caller(llm_config: dict, prompt: str) -> str:
    """Real LLM path — spins up a one-shot AG2 ConversableAgent.

    Kept as a module-level default so the synchronous ``decide_strategy``
    signature stays clean, but tests always pass their own ``llm_caller``
    so this code path isn't exercised in CI. It's still covered by the
    integration smoke test that hits a real provider.
    """
    from autogen import ConversableAgent

    meta = ConversableAgent(
        name="orchestrator-meta",
        system_message=(
            "You are an orchestrator that picks how a group of agents "
            "should collaborate. You reply only with JSON."
        ),
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    reply = meta.generate_reply(
        messages=[{"role": "user", "content": prompt}]
    )
    if isinstance(reply, dict):
        return str(reply.get("content", "") or "")
    return str(reply or "")


def _parse_decision(
    raw: str, valid_agent_ids: set[int], fallback_order: list[int]
) -> OrchestratorDecision:
    """Best-effort JSON extraction with a safe sequential fallback.

    The meta-agent is prompted to return pure JSON, but real LLMs
    sometimes wrap it in prose or code fences. We look for the first
    ``{`` / last ``}`` window before parsing, and fall back to sequential
    + position-order if anything is malformed. Defensive defaulting is
    on purpose: a misbehaving meta-agent shouldn't wedge the whole run.
    """
    text = raw.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return OrchestratorDecision(
            strategy="sequential",
            order=fallback_order,
            reasoning="fallback: meta-agent reply was not JSON",
        )
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return OrchestratorDecision(
            strategy="sequential",
            order=fallback_order,
            reasoning="fallback: meta-agent JSON was malformed",
        )

    strategy = str(parsed.get("strategy", "")).strip().lower()
    if strategy not in ("parallel", "sequential"):
        return OrchestratorDecision(
            strategy="sequential",
            order=fallback_order,
            reasoning="fallback: unknown strategy from meta-agent",
        )
    reasoning = str(parsed.get("reasoning") or "auto decision").strip()

    if strategy == "parallel":
        return OrchestratorDecision(
            strategy="parallel", order=None, reasoning=reasoning
        )

    # Sequential: validate the order list against the actual agents.
    raw_order = parsed.get("order") or []
    order: list[int] = []
    if isinstance(raw_order, list):
        for v in raw_order:
            if isinstance(v, int) and v in valid_agent_ids:
                order.append(v)
            elif isinstance(v, str) and v.isdigit() and int(v) in valid_agent_ids:
                order.append(int(v))
    # If the LLM skipped some agents, append them in position order so
    # the swarm still exercises every agent. Duplicates collapsed.
    seen = set(order)
    for aid in fallback_order:
        if aid not in seen:
            order.append(aid)
            seen.add(aid)
    if not order:
        order = fallback_order
    return OrchestratorDecision(
        strategy="sequential", order=order, reasoning=reasoning
    )


def decide_strategy(
    swarm: Swarm,
    agents: list[Agent],
    meta_provider: LLMProvider,
    *,
    llm_caller: LLMCaller | None = None,
) -> OrchestratorDecision:
    """Return the effective run strategy for ``swarm``.

    User overrides (``"parallel"`` / ``"sequential"``) short-circuit the
    meta-agent call; only ``"auto"`` consults the LLM. ``llm_caller`` is
    injectable for tests — pass your own to avoid hitting a real provider.
    """
    strategy = (swarm.orchestrator_strategy or "auto").lower()
    fallback_order = _position_order(swarm.id, agents)

    if strategy == "parallel":
        return OrchestratorDecision(
            strategy="parallel", order=None, reasoning="user override"
        )

    if strategy == "sequential":
        manual = swarm.get_manual_agent_order()
        # Keep only agent IDs that actually belong to the swarm — silently
        # drop stale entries from an older membership so we don't blow up
        # later on a KeyError in _order_agents.
        valid_ids = {a.id for a in agents}
        cleaned = [aid for aid in manual if aid in valid_ids]
        order = cleaned if cleaned else fallback_order
        return OrchestratorDecision(
            strategy="sequential", order=order, reasoning="user override"
        )

    # "auto" branch: ask the meta-agent.
    if not agents:
        return OrchestratorDecision(
            strategy="sequential",
            order=[],
            reasoning="auto fallback: swarm has no agents",
        )

    prompt = _build_meta_prompt(swarm, agents)
    call = llm_caller or _default_llm_caller
    llm_config = build_llm_config(meta_provider)
    try:
        raw = call(llm_config, prompt)
    except Exception as exc:  # pragma: no cover - defensive only
        return OrchestratorDecision(
            strategy="sequential",
            order=fallback_order,
            reasoning=f"fallback: meta-agent call failed ({exc!s})",
        )
    return _parse_decision(raw, {a.id for a in agents}, fallback_order)

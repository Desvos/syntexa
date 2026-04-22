"""Unit tests for syntexa.orchestrator.executor.run_swarm.

We mock the AG2 agent call with a custom ``agent_runner`` so no real LLM
is hit; decide_strategy's LLM branch is stubbed via
``decision_llm_caller``. Status transitions are asserted against the real
Swarm row in a fresh in-memory SQLite session per test.
"""
from __future__ import annotations

import json

import pytest
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from syntexa.core import crypto
from syntexa.models import (
    Agent,
    LLMProvider,
    Repository,
    Swarm,
    SwarmAgent,
)
from syntexa.orchestrator.executor import (
    SwarmNotFoundError,
    run_swarm,
)


@pytest.fixture(autouse=True)
def _isolated_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYNTEXA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    crypto.reset_cache_for_tests()


# --- fixtures -----------------------------------------------------------


def _seed_two_agent_swarm(
    db: Session, strategy: str = "parallel"
) -> tuple[Swarm, list[Agent], LLMProvider]:
    """Create a repo + 2 agents + 1 provider + a swarm wired to them.

    Returns the persisted rows so tests can mutate / assert on them.
    """
    provider = LLMProvider(
        name="p1",
        provider_type="openai",
        api_key_encrypted=crypto.encrypt("sk-x"),
        default_model="gpt-4o-mini",
    )
    db.add(provider)
    db.flush()

    repo = Repository(name="r1", path="/tmp/r1")
    db.add(repo)
    db.flush()

    a1 = Agent(
        name="alice",
        system_prompt="You are alice.",
        provider_id=provider.id,
    )
    a2 = Agent(
        name="bob", system_prompt="You are bob.", provider_id=provider.id
    )
    db.add_all([a1, a2])
    db.flush()

    swarm = Swarm(
        name="myswarm",
        repository_id=repo.id,
        task_description="Refactor auth",
        orchestrator_strategy=strategy,
        status="idle",
    )
    db.add(swarm)
    db.flush()

    db.add_all(
        [
            SwarmAgent(swarm_id=swarm.id, agent_id=a1.id, position=0),
            SwarmAgent(swarm_id=swarm.id, agent_id=a2.id, position=1),
        ]
    )
    db.flush()
    return swarm, [a1, a2], provider


# --- parallel strategy --------------------------------------------------


def test_parallel_runs_all_agents_and_collects_outputs(
    db_session: Session,
) -> None:
    swarm, agents, _provider = _seed_two_agent_swarm(db_session, "parallel")
    swarm_id = swarm.id

    seen_prompts: list[str] = []

    async def runner(agent: Agent, provider: LLMProvider, prompt: str) -> str:
        seen_prompts.append(f"{agent.name}:{prompt}")
        return f"{agent.name} done"

    result = run_swarm(
        swarm_id, session=db_session, agent_runner=runner
    )

    assert result.success is True
    assert result.strategy_used == "parallel"
    assert result.order is None
    assert result.agent_outputs == {
        agents[0].id: "alice done",
        agents[1].id: "bob done",
    }
    # Both agents got the SAME prompt (the task), no prior-context prefix.
    assert all("Refactor auth" in p for p in seen_prompts)
    assert not any("Previous agent outputs" in p for p in seen_prompts)

    # Status transitioned idle -> running -> completed.
    db_session.refresh(swarm)
    assert swarm.status == "completed"


# --- sequential strategy ------------------------------------------------


def test_sequential_passes_prior_outputs_as_context(
    db_session: Session,
) -> None:
    swarm, agents, _provider = _seed_two_agent_swarm(db_session, "sequential")
    swarm_id = swarm.id

    seen: list[tuple[str, str]] = []

    async def runner(agent: Agent, provider: LLMProvider, prompt: str) -> str:
        seen.append((agent.name, prompt))
        return f"[{agent.name} output]"

    result = run_swarm(
        swarm_id, session=db_session, agent_runner=runner
    )

    assert result.success is True
    assert result.strategy_used == "sequential"
    assert result.order == [agents[0].id, agents[1].id]

    # First agent gets the bare task.
    assert seen[0][0] == "alice"
    assert "Previous agent outputs" not in seen[0][1]

    # Second agent's prompt must contain the prior agent's output.
    assert seen[1][0] == "bob"
    assert "Previous agent outputs" in seen[1][1]
    assert "[alice output]" in seen[1][1]


def test_sequential_respects_manual_agent_order(
    db_session: Session,
) -> None:
    swarm, agents, _provider = _seed_two_agent_swarm(db_session, "sequential")
    # Force reversed order via manual_agent_order.
    swarm.set_manual_agent_order([agents[1].id, agents[0].id])
    db_session.flush()
    swarm_id = swarm.id

    call_order: list[str] = []

    async def runner(agent: Agent, provider: LLMProvider, prompt: str) -> str:
        call_order.append(agent.name)
        return "ok"

    result = run_swarm(
        swarm_id, session=db_session, agent_runner=runner
    )

    assert result.order == [agents[1].id, agents[0].id]
    assert call_order == ["bob", "alice"]


# --- status transitions -------------------------------------------------


def test_status_transitions_on_success(db_session: Session) -> None:
    swarm, _agents, _provider = _seed_two_agent_swarm(db_session, "parallel")
    swarm_id = swarm.id
    assert swarm.status == "idle"

    async def runner(agent: Agent, provider: LLMProvider, prompt: str) -> str:
        return "ok"

    run_swarm(swarm_id, session=db_session, agent_runner=runner)

    db_session.refresh(swarm)
    assert swarm.status == "completed"


def test_status_transitions_on_exception(db_session: Session) -> None:
    swarm, _agents, _provider = _seed_two_agent_swarm(db_session, "parallel")
    swarm_id = swarm.id

    async def runner(agent: Agent, provider: LLMProvider, prompt: str) -> str:
        raise RuntimeError("provider is on fire")

    result = run_swarm(swarm_id, session=db_session, agent_runner=runner)

    assert result.success is False
    assert "on fire" in (result.error or "")

    db_session.refresh(swarm)
    assert swarm.status == "failed"


# --- task override ------------------------------------------------------


def test_task_override_replaces_stored_description(
    db_session: Session,
) -> None:
    swarm, _agents, _provider = _seed_two_agent_swarm(db_session, "parallel")
    swarm_id = swarm.id

    prompts: list[str] = []

    async def runner(agent: Agent, provider: LLMProvider, prompt: str) -> str:
        prompts.append(prompt)
        return "ok"

    run_swarm(
        swarm_id,
        task_override="Fix the login bug instead",
        session=db_session,
        agent_runner=runner,
    )

    assert all("Fix the login bug instead" in p for p in prompts)
    assert not any("Refactor auth" in p for p in prompts)


# --- not found ----------------------------------------------------------


def test_404_when_swarm_does_not_exist(db_session: Session) -> None:
    async def runner(agent: Agent, provider: LLMProvider, prompt: str) -> str:
        return "nope"

    with pytest.raises(SwarmNotFoundError):
        run_swarm(99999, session=db_session, agent_runner=runner)


# --- meta_provider_id override ------------------------------------------


def test_uses_meta_provider_id_override_when_given(
    db_session: Session,
) -> None:
    swarm, _agents, default_provider = _seed_two_agent_swarm(
        db_session, "auto"
    )
    # Add a second provider that should be picked because we pass its id.
    other_provider = LLMProvider(
        name="other",
        provider_type="openai",
        api_key_encrypted=crypto.encrypt("sk-other"),
        default_model="gpt-4o",
    )
    db_session.add(other_provider)
    db_session.flush()
    swarm_id = swarm.id
    other_id = other_provider.id

    seen_cfgs: list[dict] = []

    def fake_llm_caller(cfg: dict, prompt: str) -> str:
        seen_cfgs.append(cfg)
        return json.dumps(
            {"strategy": "parallel", "order": [], "reasoning": "ok"}
        )

    async def runner(agent: Agent, provider: LLMProvider, prompt: str) -> str:
        return "ok"

    run_swarm(
        swarm_id,
        session=db_session,
        agent_runner=runner,
        meta_provider_id=other_id,
        decision_llm_caller=fake_llm_caller,
    )

    # The meta-agent should have been built with the override provider's
    # model, not the default agent provider's.
    assert len(seen_cfgs) == 1
    assert seen_cfgs[0]["config_list"][0]["model"] == "gpt-4o"


def test_default_meta_provider_is_first_active_agent_provider(
    db_session: Session,
) -> None:
    swarm, _agents, provider = _seed_two_agent_swarm(db_session, "auto")
    swarm_id = swarm.id

    seen_cfgs: list[dict] = []

    def fake_llm_caller(cfg: dict, prompt: str) -> str:
        seen_cfgs.append(cfg)
        return json.dumps(
            {"strategy": "parallel", "order": [], "reasoning": "ok"}
        )

    async def runner(agent: Agent, provider: LLMProvider, prompt: str) -> str:
        return "ok"

    run_swarm(
        swarm_id,
        session=db_session,
        agent_runner=runner,
        decision_llm_caller=fake_llm_caller,
    )
    # Default model of the seeded provider.
    assert seen_cfgs[0]["config_list"][0]["model"] == "gpt-4o-mini"


# --- auto strategy drives through executor ------------------------------


def test_auto_decision_flows_into_executor(db_session: Session) -> None:
    """End-to-end: auto strategy -> meta-agent picks sequential -> executor
    actually runs sequentially with the chosen order."""
    swarm, agents, _provider = _seed_two_agent_swarm(db_session, "auto")
    swarm_id = swarm.id

    def fake_llm_caller(cfg: dict, prompt: str) -> str:
        return json.dumps(
            {
                "strategy": "sequential",
                "order": [agents[1].id, agents[0].id],
                "reasoning": "bob-first",
            }
        )

    call_order: list[str] = []

    async def runner(agent: Agent, provider: LLMProvider, prompt: str) -> str:
        call_order.append(agent.name)
        return f"{agent.name} ok"

    result = run_swarm(
        swarm_id,
        session=db_session,
        agent_runner=runner,
        decision_llm_caller=fake_llm_caller,
    )

    assert result.strategy_used == "sequential"
    assert result.order == [agents[1].id, agents[0].id]
    assert call_order == ["bob", "alice"]

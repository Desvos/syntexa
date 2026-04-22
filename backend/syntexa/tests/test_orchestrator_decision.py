"""Unit tests for syntexa.orchestrator.decision.decide_strategy.

The meta-agent LLM call is injected via ``llm_caller`` so these tests
never touch a real provider. Each test builds a tiny in-memory Swarm +
Agent trio (no SQLAlchemy session needed — decide_strategy never queries
the DB directly, it works off whatever objects the caller hands it).
"""
from __future__ import annotations

import json

import pytest
from cryptography.fernet import Fernet

from syntexa.core import crypto
from syntexa.models import Agent, LLMProvider, Swarm
from syntexa.orchestrator.decision import decide_strategy


@pytest.fixture(autouse=True)
def _isolated_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Decide_strategy only calls build_llm_config when llm_caller is
    actually invoked, but we set a key anyway so an accidental real path
    doesn't crash mid-test with a confusing Fernet error."""
    monkeypatch.setenv("SYNTEXA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    crypto.reset_cache_for_tests()


def _provider() -> LLMProvider:
    p = LLMProvider()
    p.id = 1
    p.name = "meta"
    p.provider_type = "openai"
    p.base_url = None
    p.api_key_encrypted = crypto.encrypt("sk-test")
    p.default_model = "gpt-4o-mini"
    p.is_active = True
    return p


def _agent(agent_id: int, name: str = None) -> Agent:
    a = Agent()
    a.id = agent_id
    a.name = name or f"agent-{agent_id}"
    a.system_prompt = f"You are agent {agent_id}."
    a.provider_id = 1
    a.model = None
    a.is_active = True
    return a


def _swarm(strategy: str, manual_order: list[int] | None = None) -> Swarm:
    s = Swarm()
    s.id = 42
    s.name = "test-swarm"
    s.repository_id = 1
    s.task_description = "Refactor the auth module"
    s.orchestrator_strategy = strategy
    s.set_manual_agent_order(manual_order)
    s.max_rounds = 10
    s.status = "idle"
    s.is_active = True
    return s


# --- auto branch ---------------------------------------------------------


def test_auto_returns_parallel_when_llm_says_parallel() -> None:
    swarm = _swarm("auto")
    agents = [_agent(1), _agent(2)]

    def fake_caller(cfg: dict, prompt: str) -> str:
        assert "config_list" in cfg  # build_llm_config ran
        assert "agent-1" in prompt
        return json.dumps(
            {"strategy": "parallel", "order": [], "reasoning": "independent"}
        )

    decision = decide_strategy(
        swarm, agents, _provider(), llm_caller=fake_caller
    )
    assert decision.strategy == "parallel"
    assert decision.order is None
    assert "independent" in decision.reasoning


def test_auto_returns_sequential_with_explicit_order() -> None:
    swarm = _swarm("auto")
    agents = [_agent(1), _agent(2), _agent(3)]

    def fake_caller(cfg: dict, prompt: str) -> str:
        return json.dumps(
            {
                "strategy": "sequential",
                "order": [3, 1, 2],
                "reasoning": "pipeline",
            }
        )

    decision = decide_strategy(
        swarm, agents, _provider(), llm_caller=fake_caller
    )
    assert decision.strategy == "sequential"
    assert decision.order == [3, 1, 2]


def test_auto_accepts_stringy_agent_ids_in_order() -> None:
    """Meta-agents sometimes serialize ints as strings; we accept both."""
    swarm = _swarm("auto")
    agents = [_agent(1), _agent(2)]

    def fake_caller(cfg: dict, prompt: str) -> str:
        return json.dumps(
            {"strategy": "sequential", "order": ["2", "1"], "reasoning": "ok"}
        )

    decision = decide_strategy(
        swarm, agents, _provider(), llm_caller=fake_caller
    )
    assert decision.order == [2, 1]


def test_auto_fills_missing_agents_into_sequential_order() -> None:
    """If the LLM forgets an agent, we append it in position order so
    the run still exercises every agent."""
    swarm = _swarm("auto")
    agents = [_agent(1), _agent(2), _agent(3)]

    def fake_caller(cfg: dict, prompt: str) -> str:
        return json.dumps(
            {"strategy": "sequential", "order": [2], "reasoning": "partial"}
        )

    decision = decide_strategy(
        swarm, agents, _provider(), llm_caller=fake_caller
    )
    assert decision.order == [2, 1, 3]


def test_auto_falls_back_when_llm_returns_malformed_json() -> None:
    swarm = _swarm("auto")
    agents = [_agent(1), _agent(2)]

    def fake_caller(cfg: dict, prompt: str) -> str:
        return "I think parallel is best, obviously."

    decision = decide_strategy(
        swarm, agents, _provider(), llm_caller=fake_caller
    )
    # Defensive default: sequential + position order.
    assert decision.strategy == "sequential"
    assert decision.order == [1, 2]
    assert "fallback" in decision.reasoning.lower()


def test_auto_falls_back_when_llm_strategy_is_unknown() -> None:
    swarm = _swarm("auto")
    agents = [_agent(1), _agent(2)]

    def fake_caller(cfg: dict, prompt: str) -> str:
        return json.dumps(
            {"strategy": "chaotic", "order": [], "reasoning": "hmm"}
        )

    decision = decide_strategy(
        swarm, agents, _provider(), llm_caller=fake_caller
    )
    assert decision.strategy == "sequential"
    assert decision.order == [1, 2]


def test_auto_extracts_json_from_prose_wrapped_reply() -> None:
    """Real LLMs often wrap JSON in code fences or commentary. Extractor
    should locate the JSON block and parse it."""
    swarm = _swarm("auto")
    agents = [_agent(1), _agent(2)]

    def fake_caller(cfg: dict, prompt: str) -> str:
        return (
            "Sure, here's the decision:\n"
            '```json\n{"strategy":"parallel","order":[],"reasoning":"indep"}\n```'
        )

    decision = decide_strategy(
        swarm, agents, _provider(), llm_caller=fake_caller
    )
    assert decision.strategy == "parallel"


# --- user override: parallel --------------------------------------------


def test_manual_parallel_ignores_llm() -> None:
    swarm = _swarm("parallel")
    agents = [_agent(1), _agent(2)]

    def should_not_be_called(cfg: dict, prompt: str) -> str:
        raise AssertionError("llm_caller must not run for parallel override")

    decision = decide_strategy(
        swarm, agents, _provider(), llm_caller=should_not_be_called
    )
    assert decision.strategy == "parallel"
    assert decision.order is None
    assert decision.reasoning == "user override"


# --- user override: sequential ------------------------------------------


def test_manual_sequential_uses_manual_agent_order_when_set() -> None:
    swarm = _swarm("sequential", manual_order=[2, 1])
    agents = [_agent(1), _agent(2)]

    decision = decide_strategy(swarm, agents, _provider())
    assert decision.strategy == "sequential"
    assert decision.order == [2, 1]
    assert decision.reasoning == "user override"


def test_manual_sequential_falls_back_to_position_order() -> None:
    swarm = _swarm("sequential", manual_order=None)
    agents = [_agent(1), _agent(2), _agent(3)]

    decision = decide_strategy(swarm, agents, _provider())
    assert decision.strategy == "sequential"
    # Agents are passed in position order by the caller; we trust that.
    assert decision.order == [1, 2, 3]


def test_manual_sequential_drops_stale_agent_ids() -> None:
    """If manual_agent_order references an agent no longer in the swarm
    membership, we silently drop it — prevents a runtime KeyError later."""
    swarm = _swarm("sequential", manual_order=[2, 999, 1])
    agents = [_agent(1), _agent(2)]

    decision = decide_strategy(swarm, agents, _provider())
    assert decision.order == [2, 1]


# --- auto with no agents -------------------------------------------------


def test_auto_with_no_agents_returns_empty_sequential() -> None:
    swarm = _swarm("auto")
    decision = decide_strategy(swarm, [], _provider())
    assert decision.strategy == "sequential"
    assert decision.order == []

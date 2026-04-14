"""Static binding test for AG2 0.11.

AG2 churned the swarm API between 0.8 (SwarmAgent/initiate_swarm_chat)
and 0.11 (ConversableAgent/run_swarm). If they refactor again we want a
loud failure here — not a silent breakage the first time the daemon runs
against a live LLM.

This test does NOT call an LLM. It exercises only the import surface and
the agent + handoff construction that AG2SwarmEngine relies on.
"""
from __future__ import annotations

import pytest

pytest.importorskip("autogen", reason="ag2 not installed")


def test_ag2_swarm_bindings_exist() -> None:
    from autogen import ConversableAgent, run_swarm  # noqa: F401
    from autogen.agentchat.contrib.swarm_agent import AfterWorkOption  # noqa: F401
    from autogen.agentchat.group.handoffs import OnCondition  # noqa: F401
    from autogen.agentchat.group.llm_condition import StringLLMCondition  # noqa: F401
    from autogen.agentchat.group.targets.transition_target import AgentTarget  # noqa: F401


def test_ag2_handoff_graph_constructs() -> None:
    """Build the same agent+handoff graph AG2SwarmEngine builds, with
    llm_config=False so no LLM client is instantiated."""
    from autogen import ConversableAgent
    from autogen.agentchat.group.handoffs import OnCondition
    from autogen.agentchat.group.llm_condition import StringLLMCondition
    from autogen.agentchat.group.targets.transition_target import AgentTarget

    from syntexa.daemon.roles import DEFAULT_ROLES

    agents = {
        r.name: ConversableAgent(
            name=r.name, system_message=r.system_prompt, llm_config=False
        )
        for r in DEFAULT_ROLES
    }
    for role in DEFAULT_ROLES:
        handoffs = [
            OnCondition(
                target=AgentTarget(agent=agents[t]),
                condition=StringLLMCondition(prompt=f"Hand off to {t}."),
            )
            for t in role.handoff_targets
            if t in agents
        ]
        if handoffs:
            agents[role.name].register_handoffs(handoffs)

    assert set(agents) == {"planner", "coder", "tester", "reviewer"}

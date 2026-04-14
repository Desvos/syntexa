"""Swarm engine abstraction (FR-3, FR-4).

The daemon only depends on `SwarmEngine`, not on a specific agent framework.
This lets us:
- Run integration tests without installing an LLM SDK.
- Swap AG2 for autogen-agentchat or another orchestrator later (Constitution: Modular).

The concrete `AG2SwarmEngine` imports `autogen` lazily so the daemon module
is importable on machines without the agent framework installed.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol

from syntexa.daemon.roles import RoleConfig

logger = logging.getLogger(__name__)

SwarmStatus = Literal["completed", "failed", "timeout"]


@dataclass(frozen=True)
class SwarmContext:
    """Everything a swarm needs to operate on a task."""

    task_id: str
    task_name: str
    task_description: str
    task_type: str
    workspace_path: Path
    branch: str
    base_branch: str


@dataclass
class SwarmResult:
    status: SwarmStatus
    conversation_log: str
    # PR title/body the reviewer produced; used by the delivery pipeline.
    pr_title: str = ""
    pr_body: str = ""
    # Paths modified in the workspace, relative to workspace_path.
    modified_files: list[str] = field(default_factory=list)
    error: str | None = None


class SwarmEngine(Protocol):
    def run(
        self,
        roles: list[RoleConfig],
        context: SwarmContext,
        max_rounds: int,
    ) -> SwarmResult: ...


class AG2SwarmEngine:
    """AG2 (ag2>=0.11) implementation using ConversableAgent + run_swarm.

    The 0.11 rewrite of AG2 replaced SwarmAgent/initiate_swarm_chat with
    ConversableAgent + run_swarm, and moved handoff primitives under
    autogen.agentchat.group.*. All AG2 imports are local so the daemon
    module remains importable without the package installed (useful for
    the test suite, which uses a stub engine).
    """

    def __init__(
        self,
        *,
        llm_config: dict,
        allow_shell: bool = True,
    ) -> None:
        self._llm_config = llm_config
        self._allow_shell = allow_shell

    def run(
        self,
        roles: list[RoleConfig],
        context: SwarmContext,
        max_rounds: int,
    ) -> SwarmResult:
        try:
            from autogen import (  # type: ignore[import-not-found]
                ConversableAgent,
                run_swarm,
            )
            from autogen.agentchat.contrib.swarm_agent import (  # type: ignore[import-not-found]
                AfterWorkOption,
            )
            from autogen.agentchat.group.handoffs import (  # type: ignore[import-not-found]
                OnCondition,
            )
            from autogen.agentchat.group.llm_condition import (  # type: ignore[import-not-found]
                StringLLMCondition,
            )
            from autogen.agentchat.group.targets.transition_target import (  # type: ignore[import-not-found]
                AgentTarget,
            )
        except ImportError as exc:
            raise RuntimeError(
                "AG2 not installed. `pip install 'ag2>=0.11,<0.12'` to use "
                "AG2SwarmEngine."
            ) from exc

        # One agent per distinct role (a composition may list a role twice,
        # e.g. two coders — AG2 only needs a single agent instance for that role).
        role_by_name: dict[str, RoleConfig] = {r.name: r for r in roles}
        agents: dict[str, ConversableAgent] = {}
        for role in roles:
            if role.name in agents:
                continue
            agents[role.name] = ConversableAgent(
                name=role.name,
                system_message=role.system_prompt,
                llm_config=self._llm_config,
            )

        for name, agent in agents.items():
            handoffs = [
                OnCondition(
                    target=AgentTarget(agent=agents[t]),
                    condition=StringLLMCondition(prompt=f"Hand off to {t}."),
                )
                for t in role_by_name[name].handoff_targets
                if t in agents
            ]
            if handoffs:
                agent.register_handoffs(handoffs)

        initial_message = self._format_initial_message(context)
        first_agent = agents[roles[0].name]

        try:
            response = run_swarm(
                initial_agent=first_agent,
                messages=initial_message,
                agents=list(agents.values()),
                max_rounds=max_rounds,
                after_work=AfterWorkOption.TERMINATE,
            )
        except Exception as exc:  # noqa: BLE001 — swarm failure is data, not a raise
            logger.exception("Swarm %s crashed", context.task_id)
            return SwarmResult(
                status="failed",
                conversation_log="",
                error=str(exc),
            )

        return self._parse_result(response, max_rounds)

    @staticmethod
    def _format_initial_message(ctx: SwarmContext) -> str:
        return (
            f"Task: {ctx.task_name}\n"
            f"Type: {ctx.task_type}\n"
            f"Branch: {ctx.branch} (off {ctx.base_branch})\n"
            f"Workspace: {ctx.workspace_path}\n\n"
            f"Description:\n{ctx.task_description or '(no description provided)'}"
        )

    @staticmethod
    def _parse_result(response, max_rounds: int) -> SwarmResult:
        # RunResponseProtocol.messages is a property that resolves to the
        # final chat history (list[dict]).
        messages = list(getattr(response, "messages", []) or [])
        rounds_used = len(messages)
        log = "\n\n".join(
            f"[{m.get('name', '?')}] {m.get('content', '')}" for m in messages
        )
        if rounds_used >= max_rounds:
            return SwarmResult(status="timeout", conversation_log=log)

        last = messages[-1] if messages else {}
        content = last.get("content", "")
        pr_title, pr_body = _extract_pr_metadata(content)
        return SwarmResult(
            status="completed",
            conversation_log=log,
            pr_title=pr_title,
            pr_body=pr_body,
        )


def _extract_pr_metadata(reviewer_output: str) -> tuple[str, str]:
    """Pull PR title/body from the reviewer's final message.

    Expected convention: first non-empty line is the title; remainder is the body.
    Reviewer output that doesn't follow this falls back to a generic title.
    """
    lines = [ln.rstrip() for ln in reviewer_output.splitlines()]
    lines = [ln for ln in lines if ln.strip()]
    if not lines:
        return ("chore: automated change", "")
    title = lines[0].lstrip("# ").strip()
    body = "\n".join(lines[1:]).strip()
    return (title or "chore: automated change", body)

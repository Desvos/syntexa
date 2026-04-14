"""T032 — integration test: tagged task → swarm → PR.

Uses in-process fakes for both adapters and the swarm engine, so no
network, no git, no LLM. Verifies the daemon wires everything correctly.
"""
from __future__ import annotations

import threading
from pathlib import Path

from syntexa.adapters.base import (
    ProjectManagementAdapter,
    PullRequestRef,
    RepositoryAdapter,
    TaskRef,
    TaskStatus,
)
from syntexa.config import Settings
from syntexa.daemon.main import build_daemon
from syntexa.daemon.roles import RoleConfig
from syntexa.daemon.swarm import SwarmContext, SwarmResult
from syntexa.models import init_engine


class FakeClickUp(ProjectManagementAdapter):
    def __init__(self, tasks: list[TaskRef]) -> None:
        self._tasks = tasks
        self.status_updates: list[tuple[str, str]] = []
        self.comments: list[tuple[str, str]] = []

    def list_tasks(self, tag: str) -> list[TaskRef]:  # noqa: ARG002
        return list(self._tasks)

    def update_status(self, task_id: str, status: TaskStatus) -> None:
        self.status_updates.append((task_id, status))

    def add_comment(self, task_id: str, body: str) -> None:
        self.comments.append((task_id, body))

    def health_check(self) -> bool:
        return True


class FakeGitHub(RepositoryAdapter):
    def __init__(self) -> None:
        self.branches: list[tuple[str, str]] = []
        self.commits: list[tuple[str, str]] = []
        self.pushes: list[str] = []
        self.prs: list[PullRequestRef] = []

    def create_branch(self, name: str, base: str) -> None:
        self.branches.append((name, base))

    def commit(self, branch: str, message: str, paths: list[str]) -> str:  # noqa: ARG002
        self.commits.append((branch, message))
        return "sha0001"

    def push(self, branch: str) -> None:
        self.pushes.append(branch)

    def create_pr(self, head: str, base: str, title: str, body: str) -> PullRequestRef:  # noqa: ARG002
        pr = PullRequestRef(
            number=len(self.prs) + 1,
            url=f"https://example/pr/{len(self.prs) + 1}",
            branch=head,
            title=title,
        )
        self.prs.append(pr)
        return pr

    def health_check(self) -> bool:
        return True


class FakeSwarmEngine:
    def __init__(self) -> None:
        self.invocations: list[SwarmContext] = []

    def run(
        self,
        roles: list[RoleConfig],
        context: SwarmContext,
        max_rounds: int,  # noqa: ARG002
    ) -> SwarmResult:
        self.invocations.append(context)
        return SwarmResult(
            status="completed",
            conversation_log=f"[planner] ok -> [coder] done ({len(roles)} roles)",
            pr_title=f"feat({context.task_type}): {context.task_name}",
            pr_body="Automated.",
            modified_files=["README.md"],
        )


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        api_host="127.0.0.1",
        api_port=8000,
        session_secret="integration-test",
        poll_interval=10,
        max_concurrent=2,
        agent_trigger_tag="agent-swarm",
        base_branch="main",
        repo_path=tmp_path,
    )


def test_full_pipeline_tag_to_pr(tmp_path: Path) -> None:
    init_engine(f"sqlite:///{tmp_path / 'swarm.db'}")
    from syntexa.models import create_all

    create_all()

    tasks = [
        TaskRef(
            id="CU-100",
            name="Add pricing table",
            description="Build a pricing component",
            tags=("agent-swarm",),
            status="in progress",
        )
    ]
    pm = FakeClickUp(tasks)
    repo = FakeGitHub()
    engine = FakeSwarmEngine()

    poller = build_daemon(_settings(tmp_path), pm, repo, engine)
    submitted = poller.poll_once()

    assert submitted == 1

    # Wait for the swarm job (running on executor thread) to finish.
    deadline = threading.Event()
    for _ in range(100):
        if repo.prs:
            break
        deadline.wait(0.05)

    assert len(engine.invocations) == 1
    ctx = engine.invocations[0]
    assert ctx.task_id == "CU-100"
    assert ctx.task_type == "feature"
    assert ctx.branch.startswith("syntexa/CU-100-")

    feature_branches = [b for b, _base in repo.branches if b.startswith("syntexa/")]
    assert feature_branches == [ctx.branch]
    assert repo.commits and repo.commits[0][1].startswith("feat(feature):")
    assert repo.pushes == [ctx.branch]
    assert len(repo.prs) == 1

    # Status flow: in_progress → done, plus success comment with PR URL.
    statuses = [s for _, s in pm.status_updates]
    assert "in_progress" in statuses
    assert "done" in statuses
    assert any("pull request" in body.lower() for _, body in pm.comments)

    poller._executor.shutdown()  # type: ignore[attr-defined]


def test_already_active_task_is_skipped(tmp_path: Path) -> None:
    init_engine(f"sqlite:///{tmp_path / 'swarm.db'}")
    from syntexa.models import create_all

    create_all()

    tasks = [
        TaskRef(id="CU-200", name="x", description="", tags=("agent-swarm",), status="open")
    ]
    pm = FakeClickUp(tasks)
    repo = FakeGitHub()

    # Block the swarm until we release it, so we can observe the second poll
    # finding an already-active task.
    gate = threading.Event()

    class BlockingEngine:
        def __init__(self) -> None:
            self.calls = 0

        def run(self, roles, context, max_rounds):  # noqa: ARG002
            self.calls += 1
            gate.wait(timeout=2.0)
            return SwarmResult(status="completed", conversation_log="")

    engine = BlockingEngine()
    poller = build_daemon(_settings(tmp_path), pm, repo, engine)

    assert poller.poll_once() == 1
    # Second poll while first is still running.
    assert poller.poll_once() == 0

    gate.set()
    for _ in range(100):
        if engine.calls == 1 and poller._executor.active_count() == 0:  # type: ignore[attr-defined]
            break
        threading.Event().wait(0.05)

    assert engine.calls == 1
    poller._executor.shutdown()  # type: ignore[attr-defined]

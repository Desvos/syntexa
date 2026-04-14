"""Daemon entry point.

Wires together adapters, executor, swarm engine, delivery pipeline, and
poller. Run via the `syntexa-daemon` console script (see pyproject.toml).
"""
from __future__ import annotations

import logging
import signal
import sys
from datetime import datetime, timezone

from syntexa.adapters.base import ProjectManagementAdapter, RepositoryAdapter, TaskRef
from syntexa.adapters.clickup import ClickUpAdapter
from syntexa.adapters.github import GitHubAdapter
from syntexa.config import Settings, get_settings
from syntexa.daemon.classifier import classify
from syntexa.daemon.compositions import get_default_composition
from syntexa.daemon.delivery import DeliveryPipeline
from syntexa.daemon.executor import SwarmExecutor
from syntexa.daemon.poller import Poller
from syntexa.daemon.roles import DEFAULT_ROLES, RoleConfig
from syntexa.daemon.swarm import SwarmContext, SwarmEngine, SwarmResult
from syntexa.daemon.workspace import Workspace, branch_name_for
from syntexa.models import SwarmInstance, init_engine, session_scope

logger = logging.getLogger(__name__)


def build_daemon(
    settings: Settings,
    pm: ProjectManagementAdapter,
    repo: RepositoryAdapter,
    engine: SwarmEngine,
) -> Poller:
    """Factory used both by `run()` and tests."""
    executor = SwarmExecutor(max_concurrent=settings.max_concurrent)
    workspace = Workspace(repo, settings.repo_path, settings.base_branch)
    delivery = DeliveryPipeline(repo, pm)

    def job_factory(task: TaskRef):
        def job() -> None:
            _run_swarm_for_task(
                task=task,
                settings=settings,
                pm=pm,
                engine=engine,
                workspace=workspace,
                delivery=delivery,
            )

        return job

    return Poller(
        pm=pm,
        executor=executor,
        job_factory=job_factory,
        poll_interval=settings.poll_interval,
        trigger_tag=settings.agent_trigger_tag,
    )


def _run_swarm_for_task(
    *,
    task: TaskRef,
    settings: Settings,
    pm: ProjectManagementAdapter,
    engine: SwarmEngine,
    workspace: Workspace,
    delivery: DeliveryPipeline,
) -> None:
    task_type = classify(task)
    composition = get_default_composition(task_type)
    if composition is None:
        logger.error("No composition for task_type=%s; skipping %s", task_type, task.id)
        return

    roles = _roles_for(composition.roles)
    branch = branch_name_for(task.id, task.name)
    ctx = SwarmContext(
        task_id=task.id,
        task_name=task.name,
        task_description=task.description,
        task_type=task_type,
        workspace_path=workspace.path,
        branch=branch,
        base_branch=settings.base_branch,
    )

    _record_swarm_start(ctx)

    try:
        pm.update_status(task.id, "in_progress")
    except Exception:
        logger.exception("Could not mark task %s in_progress; continuing anyway", task.id)

    try:
        workspace.prepare(branch)
        result = engine.run(roles, ctx, max_rounds=composition.max_rounds)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Swarm setup failed for task %s", task.id)
        result = SwarmResult(status="failed", conversation_log="", error=str(exc))

    pr_url = delivery.deliver(ctx, result)
    _record_swarm_end(ctx, result, pr_url)
    workspace.cleanup(branch)


def _roles_for(role_names: tuple[str, ...]) -> list[RoleConfig]:
    by_name = {r.name: r for r in DEFAULT_ROLES}
    resolved: list[RoleConfig] = []
    for name in role_names:
        role = by_name.get(name)
        if role is None:
            logger.warning("Unknown role '%s' in composition; skipping", name)
            continue
        resolved.append(role)
    return resolved


def _record_swarm_start(ctx: SwarmContext) -> None:
    try:
        with session_scope() as session:
            session.add(
                SwarmInstance(
                    task_id=ctx.task_id,
                    task_name=ctx.task_name,
                    task_type=ctx.task_type,
                    branch=ctx.branch,
                    status="running",
                    started_at=datetime.now(timezone.utc),
                )
            )
    except Exception:
        logger.exception("Could not persist swarm start for %s", ctx.task_id)


def _record_swarm_end(ctx: SwarmContext, result: SwarmResult, pr_url: str | None) -> None:
    try:
        with session_scope() as session:
            instance = (
                session.query(SwarmInstance).filter_by(task_id=ctx.task_id).one_or_none()
            )
            if instance is None:
                return
            instance.status = result.status
            instance.conversation_log = result.conversation_log
            instance.pr_url = pr_url
            instance.completed_at = datetime.now(timezone.utc)
    except Exception:
        logger.exception("Could not persist swarm end for %s", ctx.task_id)


def run() -> None:
    """Console-script entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    settings.require_clickup()
    settings.require_github()

    init_engine(settings.database_url)

    pm = ClickUpAdapter(
        api_key=settings.clickup_api_key,  # type: ignore[arg-type] — require_clickup guarantees non-None
        list_id=settings.clickup_list_id,  # type: ignore[arg-type]
    )
    repo = GitHubAdapter(
        token=settings.github_token,  # type: ignore[arg-type]
        owner=settings.github_owner,  # type: ignore[arg-type]
        repo=settings.github_repo,  # type: ignore[arg-type]
        repo_path=settings.repo_path,
    )

    from syntexa.daemon.swarm import AG2SwarmEngine  # local import; AG2 is optional

    engine = AG2SwarmEngine(
        llm_config={
            "model": settings.llm_model,
            "api_key": settings.llm_api_key,
        }
    )

    poller = build_daemon(settings, pm, repo, engine)

    def _handle_signal(signum, _frame) -> None:
        logger.info("Received signal %s; shutting down", signum)
        poller.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_signal)

    try:
        poller.run_forever()
    finally:
        logger.info("Daemon exited")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        logger.exception("Daemon crashed")
        sys.exit(1)

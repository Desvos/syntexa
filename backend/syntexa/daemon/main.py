"""Daemon entry point.

Wires together adapters, executor, swarm engine, delivery pipeline, and
poller. Run via the `syntexa-daemon` console script (see pyproject.toml).
"""
from __future__ import annotations

import logging
import signal
import sys

from syntexa.adapters.base import (
    LocalRepositoryAdapter,
    NoOpProjectManagementAdapter,
    ProjectManagementAdapter,
    RepositoryAdapter,
    TaskRef,
)
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
from syntexa.models import ExternalCredential, init_engine, session_scope

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

    delivery.deliver(ctx, result)
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


def _get_clickup_credentials(settings: Settings) -> tuple[str | None, str | None] | None:
    """Resolve ClickUp credentials from env vars or database.

    Returns None if ClickUp integration is not configured.
    Returns tuple(api_key, list_id) if configured.
    """
    # Priority 1: Environment variables
    env_api_key, env_list_id = settings.get_clickup_config()
    if env_api_key and env_list_id:
        return (env_api_key, env_list_id)

    # Priority 2: Database-stored credentials
    try:
        with session_scope() as session:
            cred = (
                session.query(ExternalCredential)
                .filter_by(service_type="clickup", is_active=True)
                .first()
            )
            if cred:
                data = cred.get_credentials()
                api_key = data.get("api_key")
                list_id = data.get("list_id")
                if api_key and list_id:
                    return (api_key, list_id)
    except Exception:
        logger.debug("Could not query ClickUp credentials from database", exc_info=True)

    return None


def _get_github_credentials(settings: Settings) -> tuple[str | None, str | None, str | None] | None:
    """Resolve GitHub credentials from env vars or database.

    Returns None if GitHub integration is not configured.
    Returns tuple(token, owner, repo) if configured.
    """
    # Priority 1: Environment variables
    if settings.github_token and settings.github_owner and settings.github_repo:
        return (settings.github_token, settings.github_owner, settings.github_repo)

    # Priority 2: Database-stored credentials
    try:
        with session_scope() as session:
            cred = (
                session.query(ExternalCredential)
                .filter_by(service_type="github", is_active=True)
                .first()
            )
            if cred:
                data = cred.get_credentials()
                token = data.get("token")
                owner = data.get("owner")
                repo = data.get("repo")
                if token and owner and repo:
                    return (token, owner, repo)
    except Exception:
        logger.debug("Could not query GitHub credentials from database", exc_info=True)

    return None


def run() -> None:
    """Console-script entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()

    init_engine(settings.database_url)

    # Resolve ClickUp credentials (optional)
    clickup_creds = _get_clickup_credentials(settings)
    pm: ProjectManagementAdapter
    if clickup_creds:
        api_key, list_id = clickup_creds
        pm = ClickUpAdapter(api_key=api_key, list_id=list_id)
        logger.info("ClickUp integration configured (list_id=%s)", list_id)
    else:
        pm = NoOpProjectManagementAdapter()
        logger.warning(
            "ClickUp not configured. Using no-op adapter. Set env vars or add credentials via ExternalCredential."
        )

    # Resolve GitHub credentials (optional)
    github_creds = _get_github_credentials(settings)
    repo: RepositoryAdapter
    if github_creds:
        token, owner, repo_name = github_creds
        repo = GitHubAdapter(
            token=token, owner=owner, repo=repo_name, repo_path=settings.repo_path
        )
        logger.info("GitHub integration configured (repo=%s/%s)", owner, repo_name)
    else:
        repo = LocalRepositoryAdapter(repo_path=settings.repo_path)
        logger.warning(
            "GitHub not configured. Using local git adapter. Set env vars or add credentials via ExternalCredential."
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

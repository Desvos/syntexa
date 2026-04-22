"""CRUD endpoints for first-class Swarms, plus legacy SwarmInstance monitoring.

A Swarm is one running swarm-job instance attached to a repository, scoped
to a task. The CRUD surface here owns the new ``swarms`` table; the legacy
``/swarms/active``, ``/swarms/completed``, and ``/swarms/{id}/log`` endpoints
operate on the separate ``swarm_instances`` table and are kept in place for
monitoring until Phase 8 handles the cleanup.

Route-registration order matters: literal path segments (``/active``,
``/completed``) are declared BEFORE the parameterised ``/{swarm_id}`` routes
so FastAPI matches them even though ``swarm_id`` is typed ``int``.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from syntexa.api.dependencies import get_db
from syntexa.api.schemas import (
    AgentRead,
    SwarmCreate,
    SwarmInstanceList,
    SwarmInstanceRead,
    SwarmList,
    SwarmLogResponse,
    SwarmRead,
    SwarmRunRequest,
    SwarmRunResult,
    SwarmUpdate,
)
from syntexa.models import Agent, Repository, Swarm, SwarmAgent, SwarmInstance
from syntexa.orchestrator import run_swarm as run_swarm_impl
from syntexa.orchestrator.executor import (
    SwarmAlreadyRunningError,
    SwarmNotFoundError,
)

router = APIRouter(prefix="/swarms", tags=["swarms"])


# --- helpers -------------------------------------------------------------


def _agents_for_swarm(db: Session, swarm_id: int) -> list[Agent]:
    """Return the Agents attached to a swarm ordered by join-row position."""
    rows = (
        db.query(Agent, SwarmAgent.position)
        .join(SwarmAgent, SwarmAgent.agent_id == Agent.id)
        .filter(SwarmAgent.swarm_id == swarm_id)
        .order_by(SwarmAgent.position.asc(), Agent.id.asc())
        .all()
    )
    return [a for a, _pos in rows]


def _to_read(db: Session, swarm: Swarm) -> SwarmRead:
    agents = _agents_for_swarm(db, swarm.id)
    return SwarmRead(
        id=swarm.id,
        name=swarm.name,
        repository_id=swarm.repository_id,
        task_description=swarm.task_description,
        orchestrator_strategy=swarm.orchestrator_strategy,
        manual_agent_order=swarm.get_manual_agent_order() or None,
        max_rounds=swarm.max_rounds,
        status=swarm.status,
        is_active=swarm.is_active,
        agents=[AgentRead.model_validate(a) for a in agents],
        created_at=swarm.created_at,
        updated_at=swarm.updated_at,
    )


def _ensure_repository_exists(db: Session, repository_id: int) -> None:
    if db.get(Repository, repository_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown repository_id {repository_id}: no Repository with that id.",
        )


def _ensure_agents_exist(db: Session, agent_ids: list[int]) -> list[Agent]:
    rows = (
        db.query(Agent).filter(Agent.id.in_(agent_ids)).all()
        if agent_ids
        else []
    )
    found = {a.id for a in rows}
    missing = [aid for aid in agent_ids if aid not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown agent_id(s): {missing}",
        )
    return rows


def _replace_membership(
    db: Session, swarm: Swarm, agent_ids: list[int]
) -> None:
    """Wipe and re-insert the join rows preserving the order of ``agent_ids``."""
    db.query(SwarmAgent).filter(SwarmAgent.swarm_id == swarm.id).delete(
        synchronize_session=False
    )
    for position, aid in enumerate(agent_ids):
        db.add(SwarmAgent(swarm_id=swarm.id, agent_id=aid, position=position))


# --- legacy SwarmInstance monitoring (kept until Phase 8) ----------------


@router.get("/active", response_model=SwarmInstanceList)
def list_active_swarms(
    db: Session = Depends(get_db),
) -> SwarmInstanceList:
    """List all currently running swarms (legacy SwarmInstance)."""
    swarms = (
        db.query(SwarmInstance)
        .filter(SwarmInstance.status == "running")
        .order_by(SwarmInstance.started_at.asc())
        .all()
    )
    return SwarmInstanceList(
        swarms=[SwarmInstanceRead.model_validate(s) for s in swarms]
    )


@router.get("/completed", response_model=SwarmInstanceList)
def list_completed_swarms(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> SwarmInstanceList:
    """List recently completed swarms (legacy SwarmInstance)."""
    swarms = (
        db.query(SwarmInstance)
        .filter(SwarmInstance.status.in_(["completed", "failed", "timeout"]))
        .order_by(SwarmInstance.completed_at.desc().nullslast())
        .limit(limit)
        .all()
    )
    return SwarmInstanceList(
        swarms=[SwarmInstanceRead.model_validate(s) for s in swarms]
    )


# --- CRUD on the first-class Swarm entity --------------------------------


@router.get("", response_model=SwarmList)
def list_swarms(
    repository_id: int | None = Query(default=None, ge=1),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> SwarmList:
    q = db.query(Swarm)
    if repository_id is not None:
        q = q.filter(Swarm.repository_id == repository_id)
    if status_filter is not None:
        q = q.filter(Swarm.status == status_filter)
    rows = q.order_by(Swarm.name).all()
    return SwarmList(swarms=[_to_read(db, s) for s in rows])


@router.post(
    "",
    response_model=SwarmRead,
    status_code=status.HTTP_201_CREATED,
)
def create_swarm(
    payload: SwarmCreate,
    db: Session = Depends(get_db),
) -> SwarmRead:
    _ensure_repository_exists(db, payload.repository_id)
    _ensure_agents_exist(db, payload.agent_ids)

    swarm = Swarm(
        name=payload.name,
        repository_id=payload.repository_id,
        task_description=payload.task_description,
        orchestrator_strategy=payload.orchestrator_strategy,
        max_rounds=payload.max_rounds,
        status=payload.status,
        is_active=payload.is_active,
    )
    swarm.set_manual_agent_order(payload.manual_agent_order)
    db.add(swarm)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Swarm '{payload.name}' already exists.",
        ) from None

    for position, aid in enumerate(payload.agent_ids):
        db.add(SwarmAgent(swarm_id=swarm.id, agent_id=aid, position=position))
    db.flush()
    return _to_read(db, swarm)


@router.get("/{swarm_id}", response_model=SwarmRead)
def get_swarm(swarm_id: int, db: Session = Depends(get_db)) -> SwarmRead:
    swarm = db.get(Swarm, swarm_id)
    if swarm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Swarm not found"
        )
    return _to_read(db, swarm)


@router.patch("/{swarm_id}", response_model=SwarmRead)
def patch_swarm(
    swarm_id: int,
    payload: SwarmUpdate,
    db: Session = Depends(get_db),
) -> SwarmRead:
    swarm = db.get(Swarm, swarm_id)
    if swarm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Swarm not found"
        )

    if payload.repository_id is not None:
        _ensure_repository_exists(db, payload.repository_id)
        swarm.repository_id = payload.repository_id
    if payload.task_description is not None:
        swarm.task_description = payload.task_description
    if payload.orchestrator_strategy is not None:
        swarm.orchestrator_strategy = payload.orchestrator_strategy
    if payload.max_rounds is not None:
        swarm.max_rounds = payload.max_rounds
    if payload.status is not None:
        swarm.status = payload.status
    if payload.is_active is not None:
        swarm.is_active = payload.is_active

    if payload.agent_ids is not None:
        _ensure_agents_exist(db, payload.agent_ids)
        _replace_membership(db, swarm, payload.agent_ids)

    # Re-validate manual_agent_order against the post-merge state.
    if payload.manual_agent_order is not None:
        effective_strategy = (
            payload.orchestrator_strategy
            if payload.orchestrator_strategy is not None
            else swarm.orchestrator_strategy
        )
        if effective_strategy != "sequential":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "manual_agent_order is only valid when "
                    "orchestrator_strategy='sequential'"
                ),
            )
        effective_agent_ids = (
            payload.agent_ids
            if payload.agent_ids is not None
            else [a.id for a in _agents_for_swarm(db, swarm.id)]
        )
        extras = set(payload.manual_agent_order) - set(effective_agent_ids)
        if extras:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "manual_agent_order contains agent_ids not in agent_ids: "
                    f"{sorted(extras)}"
                ),
            )
        swarm.set_manual_agent_order(payload.manual_agent_order)

    swarm.updated_at = datetime.now(timezone.utc)
    db.flush()
    return _to_read(db, swarm)


@router.delete(
    "/{swarm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_swarm(swarm_id: int, db: Session = Depends(get_db)) -> Response:
    swarm = db.get(Swarm, swarm_id)
    if swarm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Swarm not found"
        )
    # Explicit join-row cleanup: SQLite in tests doesn't enforce
    # ondelete=CASCADE unless PRAGMA foreign_keys=ON is set, so we do it
    # in code too. In PostgreSQL the FK handles it as well — idempotent.
    db.query(SwarmAgent).filter(SwarmAgent.swarm_id == swarm_id).delete(
        synchronize_session=False
    )
    db.delete(swarm)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- orchestrator invocation --------------------------------------------


@router.post("/{swarm_id}/run", response_model=SwarmRunResult)
def run_swarm_route(
    swarm_id: int,
    payload: SwarmRunRequest | None = None,
    db: Session = Depends(get_db),
) -> SwarmRunResult:
    """Kick off the orchestrator for a swarm.

    Runs synchronously for Phase 5 — Phase 7 listeners will call the
    same ``run_swarm_impl`` from a background worker. We reuse the
    route's session so status transitions land in the same transaction
    the caller is already using (critical for the test-client setup).

    Errors:
        * 404 when ``swarm_id`` doesn't exist
        * 409 when the swarm is already in ``status="running"``
    """
    body = payload or SwarmRunRequest()
    try:
        result = run_swarm_impl(
            swarm_id,
            body.task_override,
            meta_provider_id=body.meta_provider_id,
            session=db,
        )
    except SwarmNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except SwarmAlreadyRunningError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    # Commit the swarm.status transitions written by the executor so the
    # next request sees them — run_swarm leaves that to the caller when
    # ``session`` is supplied.
    db.commit()

    return SwarmRunResult(
        swarm_id=result.swarm_id,
        strategy_used=result.strategy_used,
        order=result.order,
        agent_outputs={str(k): v for k, v in result.agent_outputs.items()},
        success=result.success,
        error=result.error,
    )


# --- legacy log endpoint (kept until Phase 8) ----------------------------


@router.get("/{swarm_id}/log", response_model=SwarmLogResponse)
def get_swarm_log(
    swarm_id: int,
    db: Session = Depends(get_db),
) -> SwarmLogResponse:
    """Get the conversation log for a legacy SwarmInstance."""
    swarm = db.get(SwarmInstance, swarm_id)
    if swarm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Swarm with id {swarm_id} not found",
        )

    return SwarmLogResponse(
        task_id=swarm.task_id,
        task_name=swarm.task_name,
        status=swarm.status,
        log=swarm.conversation_log,
        pr_url=swarm.pr_url,
        started_at=swarm.started_at,
        completed_at=swarm.completed_at,
    )

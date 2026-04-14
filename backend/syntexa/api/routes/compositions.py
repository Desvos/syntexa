"""CRUD endpoints for swarm compositions (FR-3, FR-8).

A composition binds a `task_type` to an ordered list of agent role names
plus a `max_rounds` ceiling. The daemon looks up compositions by
`task_type` at task-dispatch time. Referential integrity with
`agent_roles.name` is enforced at the app layer (roles are JSON-encoded
in the composition row, so the DB can't help us).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from syntexa.api.dependencies import get_db
from syntexa.api.schemas import (
    SwarmCompositionCreate,
    SwarmCompositionList,
    SwarmCompositionRead,
    SwarmCompositionUpdate,
)
from syntexa.models import AgentRole, SwarmComposition

router = APIRouter(prefix="/compositions", tags=["compositions"])


def _to_read(comp: SwarmComposition) -> SwarmCompositionRead:
    return SwarmCompositionRead(
        id=comp.id,
        task_type=comp.task_type,
        roles=comp.get_roles(),
        max_rounds=comp.max_rounds,
        created_at=comp.created_at,
        updated_at=comp.updated_at,
    )


def _assert_roles_exist(db: Session, role_names: list[str]) -> None:
    """Every referenced role must exist in agent_roles. Duplicates in the
    input are fine (parallel coders etc.) — we dedupe before querying."""
    distinct = set(role_names)
    found = {
        r.name
        for r in db.query(AgentRole).filter(AgentRole.name.in_(distinct)).all()
    }
    missing = sorted(distinct - found)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown roles: {', '.join(missing)}",
        )


@router.get("", response_model=SwarmCompositionList)
def list_compositions(db: Session = Depends(get_db)) -> SwarmCompositionList:
    comps = db.query(SwarmComposition).order_by(SwarmComposition.task_type).all()
    return SwarmCompositionList(compositions=[_to_read(c) for c in comps])


@router.post(
    "",
    response_model=SwarmCompositionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_composition(
    payload: SwarmCompositionCreate,
    db: Session = Depends(get_db),
) -> SwarmCompositionRead:
    _assert_roles_exist(db, payload.roles)

    comp = SwarmComposition(
        task_type=payload.task_type,
        max_rounds=payload.max_rounds,
    )
    comp.set_roles(payload.roles)
    db.add(comp)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Composition for task_type '{payload.task_type}' already exists.",
        ) from None
    return _to_read(comp)


@router.put("/{composition_id}", response_model=SwarmCompositionRead)
def update_composition(
    composition_id: int,
    payload: SwarmCompositionUpdate,
    db: Session = Depends(get_db),
) -> SwarmCompositionRead:
    comp = db.get(SwarmComposition, composition_id)
    if comp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Composition not found"
        )

    if payload.roles is not None:
        _assert_roles_exist(db, payload.roles)
        comp.set_roles(payload.roles)
    if payload.max_rounds is not None:
        comp.max_rounds = payload.max_rounds
    comp.updated_at = datetime.now(timezone.utc)

    db.flush()
    return _to_read(comp)


@router.delete(
    "/{composition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_composition(
    composition_id: int, db: Session = Depends(get_db)
) -> Response:
    comp = db.get(SwarmComposition, composition_id)
    if comp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Composition not found"
        )
    db.delete(comp)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

"""CRUD endpoints for swarm compositions (FR-3, FR-8).

A composition binds a `task_type` to an ordered list of agent role names
plus a `max_rounds` ceiling. The daemon looks up compositions by
`task_type` at task-dispatch time.

Role names in a composition are free-form: any string that passes the
pydantic slug check is accepted, and unknown names are materialized into
placeholder AgentRole rows on save so the daemon can always resolve them.
Users refine the placeholder's system_prompt later in the Roles page.
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


_PLACEHOLDER_PROMPT = (
    "Placeholder system prompt for agent role '{name}'. "
    "Edit this in the Roles page to describe the agent's responsibilities "
    "and when it should hand off."
)


def _ensure_roles(db: Session, role_names: list[str]) -> None:
    """Materialize any role names that don't yet exist in agent_roles.

    Compositions are free-form over role names; the daemon still resolves
    each name to an AgentRole at dispatch time, so we create a minimal
    placeholder row for unknown names. Duplicates in the input are fine
    — we dedupe before querying.
    """
    distinct = {n for n in role_names if n}
    if not distinct:
        return
    found = {
        r.name
        for r in db.query(AgentRole).filter(AgentRole.name.in_(distinct)).all()
    }
    for name in sorted(distinct - found):
        role = AgentRole(
            name=name,
            system_prompt=_PLACEHOLDER_PROMPT.format(name=name),
            is_default=False,
        )
        role.set_handoff_targets([])
        db.add(role)
    db.flush()


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
    _ensure_roles(db, payload.roles)

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
        _ensure_roles(db, payload.roles)
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

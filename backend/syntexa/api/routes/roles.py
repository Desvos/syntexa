"""CRUD endpoints for agent roles (FR-7).

Default roles (is_default=True) cannot be deleted — spec allows editing
them but not removal, since compositions depend on their presence.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from syntexa.api.dependencies import get_db
from syntexa.api.schemas import (
    AgentRoleCreate,
    AgentRoleList,
    AgentRoleRead,
    AgentRoleUpdate,
)
from syntexa.models import AgentRole, SwarmComposition

router = APIRouter(prefix="/roles", tags=["roles"])


def _to_read(role: AgentRole) -> AgentRoleRead:
    return AgentRoleRead(
        id=role.id,
        name=role.name,
        system_prompt=role.system_prompt,
        handoff_targets=role.get_handoff_targets(),
        is_default=role.is_default,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.get("", response_model=AgentRoleList)
def list_roles(db: Session = Depends(get_db)) -> AgentRoleList:
    roles = db.query(AgentRole).order_by(AgentRole.name).all()
    return AgentRoleList(roles=[_to_read(r) for r in roles])


@router.post("", response_model=AgentRoleRead, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: AgentRoleCreate,
    db: Session = Depends(get_db),
) -> AgentRoleRead:
    role = AgentRole(
        name=payload.name,
        system_prompt=payload.system_prompt,
        is_default=False,
    )
    role.set_handoff_targets(payload.handoff_targets)
    db.add(role)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role with name '{payload.name}' already exists.",
        ) from None
    return _to_read(role)


@router.put("/{role_id}", response_model=AgentRoleRead)
def update_role(
    role_id: int,
    payload: AgentRoleUpdate,
    db: Session = Depends(get_db),
) -> AgentRoleRead:
    role = db.get(AgentRole, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if payload.system_prompt is not None:
        role.system_prompt = payload.system_prompt
    if payload.handoff_targets is not None:
        role.set_handoff_targets(payload.handoff_targets)
    role.updated_at = datetime.now(timezone.utc)

    db.flush()
    return _to_read(role)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,  # 204 must not carry a body
)
def delete_role(role_id: int, db: Session = Depends(get_db)) -> Response:
    role = db.get(AgentRole, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_default:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Default roles cannot be deleted; edit them instead.",
        )

    # FR-7: block deletion if any composition still references this role.
    # The check is app-level (roles are JSON-encoded in composition.roles).
    compositions = db.query(SwarmComposition).all()
    in_use = [c.task_type for c in compositions if role.name in c.get_roles()]
    if in_use:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role '{role.name}' is used by compositions: {', '.join(in_use)}.",
        )

    db.delete(role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

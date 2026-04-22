"""CRUD endpoints for custom Agents.

An Agent is a (name, system_prompt, provider_id, model) bundle that a
Swarm wires up at runtime. Every Agent points at an LLMProvider — the
agent inherits `provider.default_model` unless it carries its own
`model` override.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from syntexa.api.dependencies import get_db
from syntexa.api.schemas import (
    AgentCreate,
    AgentList,
    AgentRead,
    AgentUpdate,
)
from syntexa.models import Agent, LLMProvider

router = APIRouter(prefix="/agents", tags=["agents"])


def _to_read(agent: Agent) -> AgentRead:
    return AgentRead.model_validate(agent)


def _ensure_provider_exists(db: Session, provider_id: int) -> None:
    if db.get(LLMProvider, provider_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown provider_id {provider_id}: no LLMProvider with that id.",
        )


@router.get("", response_model=AgentList)
def list_agents(db: Session = Depends(get_db)) -> AgentList:
    rows = db.query(Agent).order_by(Agent.name).all()
    return AgentList(agents=[_to_read(a) for a in rows])


@router.post(
    "",
    response_model=AgentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_agent(
    payload: AgentCreate,
    db: Session = Depends(get_db),
) -> AgentRead:
    _ensure_provider_exists(db, payload.provider_id)

    agent = Agent(
        name=payload.name,
        system_prompt=payload.system_prompt,
        provider_id=payload.provider_id,
        model=payload.model,
        is_active=payload.is_active,
    )
    db.add(agent)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent '{payload.name}' already exists.",
        ) from None
    return _to_read(agent)


@router.put("/{agent_id}", response_model=AgentRead)
def update_agent(
    agent_id: int,
    payload: AgentUpdate,
    db: Session = Depends(get_db),
) -> AgentRead:
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    if payload.provider_id is not None:
        _ensure_provider_exists(db, payload.provider_id)
        agent.provider_id = payload.provider_id
    if payload.system_prompt is not None:
        agent.system_prompt = payload.system_prompt
    if payload.model is not None:
        agent.model = payload.model
    if payload.is_active is not None:
        agent.is_active = payload.is_active
    agent.updated_at = datetime.now(timezone.utc)

    db.flush()
    return _to_read(agent)


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_agent(agent_id: int, db: Session = Depends(get_db)) -> Response:
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    db.delete(agent)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

"""Swarm monitoring endpoints (FR-10).

Provides visibility into active and completed swarm instances,
including conversation logs and execution status.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from syntexa.api.dependencies import get_db
from syntexa.api.schemas import (
    SwarmInstanceList,
    SwarmInstanceRead,
    SwarmLogResponse,
)
from syntexa.models import SwarmInstance

router = APIRouter(prefix="/swarms", tags=["swarms"])


@router.get("/active", response_model=SwarmInstanceList)
def list_active_swarms(
    db: Session = Depends(get_db),
) -> SwarmInstanceList:
    """List all currently running swarms.

    Returns swarms with status 'running', ordered by start time (oldest first).
    """
    swarms = (
        db.query(SwarmInstance)
        .filter(SwarmInstance.status == "running")
        .order_by(SwarmInstance.started_at.asc())
        .all()
    )

    return SwarmInstanceList(
        swarms=[
            SwarmInstanceRead(
                id=s.id,
                task_id=s.task_id,
                task_name=s.task_name,
                task_type=s.task_type,
                branch=s.branch,
                status=s.status,
                active_agent=s.active_agent,
                pr_url=s.pr_url,
                started_at=s.started_at,
                completed_at=s.completed_at,
            )
            for s in swarms
        ]
    )


@router.get("/completed", response_model=SwarmInstanceList)
def list_completed_swarms(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> SwarmInstanceList:
    """List recently completed swarms.

    Returns swarms with status 'completed', 'failed', or 'timeout',
    ordered by completion time (most recent first).
    """
    swarms = (
        db.query(SwarmInstance)
        .filter(SwarmInstance.status.in_(["completed", "failed", "timeout"]))
        .order_by(SwarmInstance.completed_at.desc().nullslast())
        .limit(limit)
        .all()
    )

    return SwarmInstanceList(
        swarms=[
            SwarmInstanceRead(
                id=s.id,
                task_id=s.task_id,
                task_name=s.task_name,
                task_type=s.task_type,
                branch=s.branch,
                status=s.status,
                active_agent=s.active_agent,
                pr_url=s.pr_url,
                started_at=s.started_at,
                completed_at=s.completed_at,
            )
            for s in swarms
        ]
    )


@router.get("/{swarm_id}/log", response_model=SwarmLogResponse)
def get_swarm_log(
    swarm_id: int,
    db: Session = Depends(get_db),
) -> SwarmLogResponse:
    """Get the conversation log for a specific swarm.

    Returns the full conversation history including agent handoffs.
    """
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

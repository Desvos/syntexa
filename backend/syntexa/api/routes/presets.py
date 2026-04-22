"""Read-only catalogs + a POST apply endpoint for built-in presets.

The catalogs expose the raw preset dicts so the frontend can render
picker UIs without having to hard-code the list. ``POST /presets/apply``
is the write-through: it seeds the preset into the DB and returns the
created entity.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from syntexa.api.dependencies import get_db
from syntexa.api.schemas import (
    AgentPresetRead,
    AgentRead,
    LLMProviderRead,
    PresetApplyRequest,
    PresetApplyResponse,
    ProviderPresetRead,
    SwarmRead,
    SwarmTemplateRead,
)
from syntexa.api.routes.llm_providers import _to_read as _provider_to_read
from syntexa.api.routes.swarms import _to_read as _swarm_to_read
from syntexa.models import Agent, LLMProvider, Swarm
from syntexa.presets import (
    BUILTIN_AGENT_PRESETS,
    BUILTIN_PROVIDER_PRESETS,
    BUILTIN_SWARM_TEMPLATES,
    apply_preset,
)
from syntexa.presets.apply import (
    InvalidOverrideError,
    UnknownPresetError,
)

router = APIRouter(prefix="/presets", tags=["presets"])


# --- read-only catalogs --------------------------------------------------


@router.get("/agents", response_model=list[AgentPresetRead])
def list_agent_presets() -> list[AgentPresetRead]:
    return [AgentPresetRead(**entry) for entry in BUILTIN_AGENT_PRESETS]


@router.get("/providers", response_model=list[ProviderPresetRead])
def list_provider_presets() -> list[ProviderPresetRead]:
    return [ProviderPresetRead(**entry) for entry in BUILTIN_PROVIDER_PRESETS]


@router.get("/swarm-templates", response_model=list[SwarmTemplateRead])
def list_swarm_templates() -> list[SwarmTemplateRead]:
    return [SwarmTemplateRead(**entry) for entry in BUILTIN_SWARM_TEMPLATES]


# --- write-through apply -------------------------------------------------


@router.post(
    "/apply",
    response_model=PresetApplyResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply(
    payload: PresetApplyRequest,
    db: Session = Depends(get_db),
) -> PresetApplyResponse:
    try:
        entity = apply_preset(
            payload.kind,
            payload.preset_name,
            db,
            **(payload.overrides or {}),
        )
    except UnknownPresetError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except InvalidOverrideError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Preset '{payload.preset_name}' conflicts with an existing row.",
        ) from exc

    if isinstance(entity, Agent):
        return PresetApplyResponse(
            kind="agent",
            agent=AgentRead.model_validate(entity),
        )
    if isinstance(entity, LLMProvider):
        return PresetApplyResponse(
            kind="provider",
            provider=_provider_to_read(entity),
        )
    if isinstance(entity, Swarm):
        return PresetApplyResponse(
            kind="swarm_template",
            swarm=_swarm_to_read(db, entity),
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unexpected entity type from preset: {type(entity).__name__}",
    )

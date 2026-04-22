"""CRUD endpoints for LLM providers.

A provider is a (name, type, base_url, api_key, default_model) bundle an
Agent can point at. The api_key is encrypted at rest and never echoed back
verbatim — responses only carry a masked preview.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from syntexa.api.dependencies import get_db
from syntexa.api.schemas import (
    LLMProviderCreate,
    LLMProviderList,
    LLMProviderRead,
    LLMProviderUpdate,
)
from syntexa.core.crypto import decrypt, encrypt
from syntexa.llm.provider_config import mask_key
from syntexa.models import LLMProvider

router = APIRouter(prefix="/llm-providers", tags=["llm-providers"])


def _to_read(provider: LLMProvider) -> LLMProviderRead:
    preview: str | None = None
    if provider.api_key_encrypted:
        try:
            preview = mask_key(decrypt(provider.api_key_encrypted))
        except Exception:
            preview = "<unreadable>"
    return LLMProviderRead(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type,
        base_url=provider.base_url,
        api_key_preview=preview,
        default_model=provider.default_model,
        is_active=provider.is_active,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


@router.get("", response_model=LLMProviderList)
def list_providers(db: Session = Depends(get_db)) -> LLMProviderList:
    rows = db.query(LLMProvider).order_by(LLMProvider.name).all()
    return LLMProviderList(providers=[_to_read(p) for p in rows])


@router.post(
    "",
    response_model=LLMProviderRead,
    status_code=status.HTTP_201_CREATED,
)
def create_provider(
    payload: LLMProviderCreate,
    db: Session = Depends(get_db),
) -> LLMProviderRead:
    provider = LLMProvider(
        name=payload.name,
        provider_type=payload.provider_type,
        base_url=payload.base_url,
        api_key_encrypted=encrypt(payload.api_key) if payload.api_key else None,
        default_model=payload.default_model,
        is_active=payload.is_active,
    )
    db.add(provider)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Provider '{payload.name}' already exists.",
        ) from None
    return _to_read(provider)


@router.put("/{provider_id}", response_model=LLMProviderRead)
def update_provider(
    provider_id: int,
    payload: LLMProviderUpdate,
    db: Session = Depends(get_db),
) -> LLMProviderRead:
    provider = db.get(LLMProvider, provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )

    if payload.base_url is not None:
        provider.base_url = payload.base_url
    if payload.api_key is not None:
        provider.api_key_encrypted = encrypt(payload.api_key) if payload.api_key else None
    if payload.default_model is not None:
        provider.default_model = payload.default_model
    if payload.is_active is not None:
        provider.is_active = payload.is_active
    provider.updated_at = datetime.now(timezone.utc)

    db.flush()
    return _to_read(provider)


@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_provider(provider_id: int, db: Session = Depends(get_db)) -> Response:
    provider = db.get(LLMProvider, provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    db.delete(provider)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

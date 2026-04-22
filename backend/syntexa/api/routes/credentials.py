"""External credentials management endpoints.

Stores service credentials (ClickUp, GitHub, etc.) in the database
to avoid environment variable configuration requirements.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from syntexa.api.dependencies import get_db
from syntexa.api.schemas import (
    ConnectionStatus,
    ExternalCredentialCreate,
    ExternalCredentialRead,
    ExternalCredentialUpdate,
    SettingsStatusResponse,
)
from syntexa.config import get_settings
from syntexa.config.settings import Settings
from syntexa.models import ExternalCredential
from syntexa.models.database import session_scope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credentials", tags=["credentials"])


def _get_credential_from_db(db: Session, credential_id: int) -> ExternalCredential | None:
    """Fetch a credential by ID."""
    return db.get(ExternalCredential, credential_id)


def _get_clickup_creds(settings: Settings) -> tuple[str | None, str | None]:
    """Resolve ClickUp credentials from env vars or database."""
    env_key, env_list = settings.get_clickup_config()
    if env_key and env_list:
        return (env_key, env_list)

    try:
        with session_scope() as db:
            cred = (
                db.query(ExternalCredential)
                .filter_by(service_type="clickup", is_active=True)
                .first()
            )
            if cred:
                data = cred.get_credentials()
                return (data.get("api_key"), data.get("list_id"))
    except Exception:
        logger.debug("Could not query ClickUp credentials from database", exc_info=True)

    return (None, None)


def _get_github_creds(
    settings: Settings,
) -> tuple[str | None, str | None, str | None]:
    """Resolve GitHub credentials from env vars or database."""
    if settings.github_token and settings.github_owner and settings.github_repo:
        return (settings.github_token, settings.github_owner, settings.github_repo)

    try:
        with session_scope() as db:
            cred = (
                db.query(ExternalCredential)
                .filter_by(service_type="github", is_active=True)
                .first()
            )
            if cred:
                data = cred.get_credentials()
                return (
                    data.get("token"),
                    data.get("owner"),
                    data.get("repo"),
                )
    except Exception:
        logger.debug("Could not query GitHub credentials from database", exc_info=True)

    return (None, None, None)


def _get_credential_fields(service_type: str) -> list[str]:
    """Return expected credential fields for a service type."""
    fields = {
        "clickup": ["api_key", "list_id"],
        "github": ["token", "owner", "repo"],
        "jira": ["api_token", "domain", "email"],
        "linear": ["api_key"],
        "gitlab": ["token", "url"],
        "custom": ["config"],
    }
    return fields.get(service_type.lower(), [])


@router.get("", response_model=list[ExternalCredentialRead])
def list_credentials(db: Session = Depends(get_db)) -> list[ExternalCredentialRead]:
    """List all stored external credentials (without sensitive data)."""
    creds = db.query(ExternalCredential).all()
    return [
        ExternalCredentialRead(
            id=c.id,
            service_type=c.service_type,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in creds
    ]


@router.post("", response_model=ExternalCredentialRead, status_code=status.HTTP_201_CREATED)
def create_credential(
    payload: ExternalCredentialCreate,
    db: Session = Depends(get_db),
) -> ExternalCredentialRead:
    """Create a new external credential."""
    # Validate credentials contain required fields
    required_fields = _get_credential_fields(payload.service_type)
    missing = [f for f in required_fields if f not in payload.credentials]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required fields for {payload.service_type}: {', '.join(missing)}",
        )

    cred = ExternalCredential(
        service_type=payload.service_type,
        is_active=payload.is_active,
    )
    cred.set_credentials(payload.credentials)
    db.add(cred)
    db.commit()
    db.refresh(cred)

    logger.info("Created credential for service=%s (id=%s)", cred.service_type, cred.id)

    return ExternalCredentialRead(
        id=cred.id,
        service_type=cred.service_type,
        is_active=cred.is_active,
        created_at=cred.created_at,
        updated_at=cred.updated_at,
    )


@router.get("/{credential_id}", response_model=ExternalCredentialRead)
def get_credential(
    credential_id: int,
    db: Session = Depends(get_db),
) -> ExternalCredentialRead:
    """Get a specific credential (without sensitive data)."""
    cred = _get_credential_from_db(db, credential_id)
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential {credential_id} not found",
        )

    return ExternalCredentialRead(
        id=cred.id,
        service_type=cred.service_type,
        is_active=cred.is_active,
        created_at=cred.created_at,
        updated_at=cred.updated_at,
    )


@router.patch("/{credential_id}", response_model=ExternalCredentialRead)
def update_credential(
    credential_id: int,
    payload: ExternalCredentialUpdate,
    db: Session = Depends(get_db),
) -> ExternalCredentialRead:
    """Update a credential (partial update)."""
    cred = _get_credential_from_db(db, credential_id)
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential {credential_id} not found",
        )

    updates = payload.model_dump(exclude_unset=True)

    if "is_active" in updates:
        cred.is_active = updates["is_active"]

    if "credentials" in updates and updates["credentials"]:
        # Merge with existing credentials
        existing = cred.get_credentials()
        existing.update(updates["credentials"])
        cred.set_credentials(existing)

    db.commit()
    db.refresh(cred)

    logger.info("Updated credential id=%s", cred.id)

    return ExternalCredentialRead(
        id=cred.id,
        service_type=cred.service_type,
        is_active=cred.is_active,
        created_at=cred.created_at,
        updated_at=cred.updated_at,
    )


@router.delete("/{credential_id}", status_code=status.HTTP_200_OK)
def delete_credential(
    credential_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a credential."""
    cred = _get_credential_from_db(db, credential_id)
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential {credential_id} not found",
        )

    db.delete(cred)
    db.commit()
    logger.info("Deleted credential id=%s", credential_id)

    return {"message": f"Credential {credential_id} deleted"}


@router.get("/status/connections", response_model=SettingsStatusResponse)
def get_connection_status() -> SettingsStatusResponse:
    """Get connection health status for external services.

    Combines both environment variables and database credentials.
    """
    settings = get_settings()
    connections: list[ConnectionStatus] = []

    # Check ClickUp
    clickup_key, clickup_list = _get_clickup_creds(settings)
    if clickup_key and clickup_list:
        connections.append(
            ConnectionStatus(
                service="clickup",
                status="configured",
                message="ClickUp API key and list ID configured",
            )
        )
    else:
        connections.append(
            ConnectionStatus(
                service="clickup",
                status="unconfigured",
                message="Missing ClickUp credentials (env vars or database)",
            )
        )

    # Check GitHub
    github_token, github_owner, github_repo = _get_github_creds(settings)
    if github_token and github_owner and github_repo:
        connections.append(
            ConnectionStatus(
                service="github",
                status="configured",
                message="GitHub token, owner and repo configured",
            )
        )
    else:
        missing = []
        if not github_token:
            missing.append("token")
        if not github_owner:
            missing.append("owner")
        if not github_repo:
            missing.append("repo")
        connections.append(
            ConnectionStatus(
                service="github",
                status="unconfigured",
                message=f"Missing GitHub credentials (fields: {', '.join(missing)})",
            )
        )

    return SettingsStatusResponse(connections=connections)


def get_credential_with_secrets(
    credential_id: int,
    db: Session,
) -> dict[str, Any] | None:
    """Internal helper to get credential with secrets (for daemon use).

    This is not exposed via REST API - only internal use.
    """
    cred = db.get(ExternalCredential, credential_id)
    if not cred or not cred.is_active:
        return None
    return cred.get_credentials()

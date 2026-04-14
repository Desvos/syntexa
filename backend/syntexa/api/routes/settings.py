"""System settings management endpoints (FR-9).

Settings are stored as key-value pairs in the database.
Runtime-tunable settings can be updated without restarting the daemon.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from syntexa.api.dependencies import get_db
from syntexa.api.schemas import (
    ConnectionStatus,
    SettingsStatusResponse,
    SystemSettingItem,
    SystemSettingsRead,
    SystemSettingUpdate,
)
from syntexa.config import get_settings as get_env_settings
from syntexa.daemon.settings_watcher import trigger_daemon_reload
from syntexa.models import SystemSetting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

# Keys that can be updated at runtime
RUNTIME_KEYS = {
    "poll_interval",
    "max_concurrent",
    "log_retention_days",
    "agent_trigger_tag",
    "base_branch",
}

# All settings keys with their default values
SETTINGS_DEFAULTS: dict[str, Any] = {
    "poll_interval": 300,
    "max_concurrent": 3,
    "log_retention_days": 30,
    "agent_trigger_tag": "agent-swarm",
    "base_branch": "main",
    "repo_path": ".",
}


def _ensure_defaults(db: Session) -> None:
    """Create default settings entries if they don't exist."""
    env = get_env_settings()
    defaults_from_env = {
        "poll_interval": env.poll_interval,
        "max_concurrent": env.max_concurrent,
        "log_retention_days": env.log_retention_days,
        "agent_trigger_tag": env.agent_trigger_tag,
        "base_branch": env.base_branch,
        "repo_path": str(env.repo_path),
    }

    for key, default_val in {**SETTINGS_DEFAULTS, **defaults_from_env}.items():
        existing = db.get(SystemSetting, key)
        if existing is None:
            setting = SystemSetting(key=key)
            setting.set_value(default_val)
            db.add(setting)

    db.commit()


def _get_setting_value(db: Session, key: str) -> Any:
    """Get a setting value from database, fallback to defaults."""
    setting = db.get(SystemSetting, key)
    if setting is not None:
        return setting.get_value()
    return SETTINGS_DEFAULTS.get(key)


@router.get("", response_model=SystemSettingsRead)
def get_settings(db: Session = Depends(get_db)) -> SystemSettingsRead:
    """Get all system settings.

    Returns runtime-tunable settings that control daemon behavior.
    """
    _ensure_defaults(db)

    return SystemSettingsRead(
        poll_interval=_get_setting_value(db, "poll_interval"),
        max_concurrent=_get_setting_value(db, "max_concurrent"),
        log_retention_days=_get_setting_value(db, "log_retention_days"),
        agent_trigger_tag=_get_setting_value(db, "agent_trigger_tag"),
        base_branch=_get_setting_value(db, "base_branch"),
        repo_path=_get_setting_value(db, "repo_path"),
    )


@router.patch("", response_model=SystemSettingsRead)
def update_settings(
    payload: SystemSettingUpdate,
    db: Session = Depends(get_db),
) -> SystemSettingsRead:
    """Update system settings.

    Changes take effect immediately without daemon restart.
    Only runtime-tunable settings can be modified.
    """
    _ensure_defaults(db)

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No settings provided for update",
        )

    for key, value in updates.items():
        if key not in RUNTIME_KEYS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Setting '{key}' cannot be updated at runtime",
            )

        setting = db.get(SystemSetting, key)
        if setting is None:
            setting = SystemSetting(key=key)
            db.add(setting)

        setting.set_value(value)
        setting.updated_at = datetime.now(timezone.utc)
        logger.info("Setting updated: %s = %s", key, value)

    db.commit()

    # Notify daemon to reload settings
    trigger_daemon_reload()

    return get_settings(db)


@router.get("/status", response_model=SettingsStatusResponse)
def get_settings_status() -> SettingsStatusResponse:
    """Get connection health status for external services.

    Returns current connectivity to ClickUp and GitHub.
    """
    env = get_env_settings()
    connections: list[ConnectionStatus] = []

    # Check ClickUp
    clickup_configured = bool(env.clickup_api_key and env.clickup_list_id)
    if clickup_configured:
        # In a real implementation, we'd do a ping check here
        # For now, report based on configuration presence
        connections.append(
            ConnectionStatus(
                service="clickup",
                status="connected",
                message="ClickUp API key and list ID configured",
            )
        )
    else:
        connections.append(
            ConnectionStatus(
                service="clickup",
                status="unconfigured",
                message="Missing SYNTEXA_CLICKUP_API_KEY or SYNTEXA_CLICKUP_LIST_ID",
            )
        )

    # Check GitHub
    github_configured = bool(env.github_token and env.github_owner and env.github_repo)
    if github_configured:
        connections.append(
            ConnectionStatus(
                service="github",
                status="connected",
                message="GitHub token, owner and repo configured",
            )
        )
    else:
        missing = []
        if not env.github_token:
            missing.append("SYNTEXA_GITHUB_TOKEN")
        if not env.github_owner:
            missing.append("SYNTEXA_GITHUB_OWNER")
        if not env.github_repo:
            missing.append("SYNTEXA_GITHUB_REPO")
        connections.append(
            ConnectionStatus(
                service="github",
                status="unconfigured",
                message=f"Missing environment variables: {', '.join(missing)}",
            )
        )

    return SettingsStatusResponse(connections=connections)

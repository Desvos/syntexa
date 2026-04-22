"""Environment-backed configuration with validation.

Values are sourced from environment variables (optionally via a `.env` file).
Runtime-tunable fields (poll_interval, max_concurrent, log_retention_days) can
be overridden per-request from the `system_settings` table; this module only
provides boot-time defaults.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SYNTEXA_",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Storage ---------------------------------------------------------
    database_url: str = Field(
        default="sqlite:///./syntexa.db",
        description="SQLAlchemy database URL. SQLite is the default/recommended backend.",
    )

    # --- API / dashboard -------------------------------------------------
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000, ge=1, le=65535)
    session_secret: str = Field(
        default="change-me",
        description="HMAC secret for session cookies. MUST be overridden in production.",
        min_length=8,
    )

    # --- Daemon defaults (mirrored into system_settings on first boot) ---
    poll_interval: int = Field(default=300, ge=10, description="Seconds between ClickUp polls.")
    max_concurrent: int = Field(default=3, ge=1, description="Max swarms running in parallel.")
    log_retention_days: int = Field(default=30, ge=1)
    agent_trigger_tag: str = Field(default="agent-swarm")
    base_branch: str = Field(default="main")
    repo_path: Path = Field(
        default=Path("."),
        description="Local checkout of the target repository the swarm edits.",
    )

    # --- External service credentials -----------------------------------
    clickup_api_key: str | None = Field(default=None)
    clickup_list_id: str | None = Field(default=None)
    github_token: str | None = Field(default=None)
    github_owner: str | None = Field(default=None)
    github_repo: str | None = Field(default=None)

    # --- LLM -------------------------------------------------------------
    llm_provider: str = Field(default="anthropic")
    llm_model: str = Field(default="claude-opus-4-6")
    llm_api_key: str | None = Field(default=None)

    @field_validator("repo_path")
    @classmethod
    def _resolve_repo_path(cls, v: Path) -> Path:
        return v.expanduser().resolve()

    def get_clickup_config(self) -> tuple[str | None, str | None]:
        """Return (api_key, list_id) if configured via env vars, else (None, None).
        For database-stored credentials, use ExternalCredential model instead."""
        return (self.clickup_api_key, self.clickup_list_id)

    def require_github(self) -> None:
        if not (self.github_token and self.github_owner and self.github_repo):
            raise RuntimeError(
                "GitHub not configured: set SYNTEXA_GITHUB_TOKEN, "
                "SYNTEXA_GITHUB_OWNER and SYNTEXA_GITHUB_REPO."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance. Clear the cache in tests with
    `get_settings.cache_clear()` before re-reading env."""
    return Settings()

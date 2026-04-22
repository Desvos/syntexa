"""SQLAlchemy ORM entities mirroring data-model.md."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from syntexa.models.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentRole(Base):
    __tablename__ = "agent_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON-encoded list[str] of role names this agent can hand off to.
    handoff_targets: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    def get_handoff_targets(self) -> list[str]:
        raw = json.loads(self.handoff_targets or "[]")
        if not isinstance(raw, list):
            return []
        # Legacy rows stored objects like {"type": "...", "name": "..."}; normalize per-element.
        out: list[str] = []
        for t in raw:
            if isinstance(t, str):
                out.append(t)
            elif isinstance(t, dict) and t.get("name"):
                out.append(str(t["name"]))
        return out

    def set_handoff_targets(self, targets: list[str]) -> None:
        self.handoff_targets = json.dumps(list(targets))


class SwarmComposition(Base):
    __tablename__ = "swarm_compositions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    # JSON-encoded ordered list[str] of role names.
    roles: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    max_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    def get_roles(self) -> list[str]:
        return json.loads(self.roles or "[]")

    def set_roles(self, role_names: list[str]) -> None:
        self.roles = json.dumps(list(role_names))


class SwarmInstance(Base):
    __tablename__ = "swarm_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    task_name: Mapped[str] = mapped_column(String(256), nullable=False)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    branch: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    active_agent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    conversation_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    pr_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    __table_args__ = (
        Index("ix_swarm_instances_status_completed", "status", "completed_at"),
    )


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    # JSON-encoded scalar or structured value.
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    def get_value(self) -> Any:
        return json.loads(self.value)

    def set_value(self, value: Any) -> None:
        self.value = json.dumps(value)


class LLMProvider(Base):
    """An LLM endpoint + credential the user has registered.

    Supports native APIs (anthropic, openai) and OpenAI-compatible endpoints
    (openrouter, ollama, generic). The API key is encrypted at rest via
    `syntexa.core.crypto` — the column stores a Fernet ciphertext, never
    plaintext. Nullable for Ollama-style local endpoints that don't auth.
    """

    __tablename__ = "llm_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_model: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )


class ExternalCredential(Base):
    """Stores external service credentials (ClickUp, GitHub, etc.) in the database.

    Credentials are encrypted at rest and scoped by service_type.
    """
    __tablename__ = "external_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # JSON-encoded dict with service-specific fields (api_key, list_id, etc.)
    _credentials: Mapped[str] = mapped_column("credentials", Text, nullable=False, default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    def get_credentials(self) -> dict[str, Any]:
        return json.loads(self._credentials)

    def set_credentials(self, value: dict[str, Any]) -> None:
        self._credentials = json.dumps(value)

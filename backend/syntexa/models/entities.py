"""SQLAlchemy ORM entities mirroring data-model.md."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
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


class Agent(Base):
    """A user-defined agent bound to an LLMProvider.

    Replaces the legacy hardcoded AgentRole roster: users freely create
    agents by giving them a name, a system prompt, a provider, and
    optionally a model override. When `model` is NULL, the agent inherits
    `provider.default_model` at config-build time.

    The legacy `AgentRole` table stays in place for now — Phase 8 handles
    the cleanup + migration.
    """

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    provider_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("llm_providers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
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


class Repository(Base):
    """A code repository the platform can run swarms against.

    Multi-repo first class: each row is a (name, path, remote_url, default_branch,
    clickup_list_id) bundle. Worktrees created by the daemon will scope to one
    specific repo, enabling concurrent swarms on different codebases. The
    `path` is an absolute location on disk — the row can exist before the path
    is materialized; the /health endpoint surfaces disk reality.
    """

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    remote_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    default_branch: Mapped[str] = mapped_column(
        String(128), nullable=False, default="main"
    )
    clickup_list_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )


class Swarm(Base):
    """A first-class running swarm-job instance attached to a repository.

    A Swarm binds N agents to one repository for a specific task. The
    orchestrator_strategy decides how the agents take turns:

    - ``auto``: let the framework pick (group-chat style)
    - ``parallel``: fan out simultaneously
    - ``sequential``: walk agents in a fixed order (see
      ``manual_agent_order``)

    Replaces the legacy ``SwarmComposition`` concept (task-type keyed).
    The legacy ``SwarmComposition`` and ``SwarmInstance`` tables stay in
    place for now — Phase 8 handles the cleanup + migration.
    """

    __tablename__ = "swarms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    repository_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("repositories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    task_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    orchestrator_strategy: Mapped[str] = mapped_column(
        String(16), nullable=False, default="auto"
    )
    # JSON-encoded list[int] of agent IDs, only used when strategy=sequential.
    manual_agent_order: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="idle", index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    def get_manual_agent_order(self) -> list[int]:
        raw = json.loads(self.manual_agent_order or "[]")
        if not isinstance(raw, list):
            return []
        out: list[int] = []
        for v in raw:
            if isinstance(v, int):
                out.append(v)
            elif isinstance(v, str) and v.isdigit():
                out.append(int(v))
        return out

    def set_manual_agent_order(self, order: list[int] | None) -> None:
        if order is None:
            self.manual_agent_order = None
        else:
            self.manual_agent_order = json.dumps([int(i) for i in order])


class SwarmAgent(Base):
    """Join row for the N:M Swarm <-> Agent relationship.

    A swarm has multiple agents; an agent can be in multiple swarms.
    ``position`` is the display-order within the swarm (0-based). The
    swarm side cascades on delete; the agent side restricts so deleting
    an agent that's still wired into a swarm fails loudly.
    """

    __tablename__ = "swarm_agents"

    swarm_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("swarms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agents.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

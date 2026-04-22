"""Pydantic request/response schemas for the HTTP API.

Keep these separate from ORM entities: the DB stores handoff_targets as a
JSON-encoded string, but clients send/receive a real list[str]. The route
handlers do the translation.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# --- User ----------------------------------------------------------------

class UserCreate(BaseModel):
    """Create a new user."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def _username_is_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("username cannot be empty")
        if not all(c.isalnum() or c in ("-", "_") for c in v):
            raise ValueError("username must be alphanumeric with - or _")
        return v

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class UserRead(BaseModel):
    """User data for API responses (excludes password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime
    last_login_at: datetime | None


class UserList(BaseModel):
    """List of users."""

    users: list[UserRead]


class LoginRequest(BaseModel):
    """Login credentials."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Successful login response with session token."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead


class UserDeleteResponse(BaseModel):
    """Response for user deletion."""

    message: str
    deleted_user_id: int


class AgentRoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    system_prompt: str = Field(..., min_length=1)
    handoff_targets: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _name_is_slug(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        if not all(c.isalnum() or c in ("-", "_") for c in v):
            raise ValueError("name must be alphanumeric with - or _")
        return v.lower()

    @field_validator("handoff_targets")
    @classmethod
    def _unique_targets(cls, v: list[str]) -> list[str]:
        if len(v) != len(set(v)):
            raise ValueError("handoff_targets must be unique")
        return v


class AgentRoleUpdate(BaseModel):
    """Partial update — only supplied fields are changed.

    `name` is intentionally NOT updatable: compositions reference roles by
    name, and renaming would silently break them. Users delete+recreate
    instead.
    """

    system_prompt: str | None = Field(default=None, min_length=1)
    handoff_targets: list[str] | None = None

    @field_validator("handoff_targets")
    @classmethod
    def _unique_targets(cls, v: list[str] | None) -> list[str] | None:
        if v is not None and len(v) != len(set(v)):
            raise ValueError("handoff_targets must be unique")
        return v


class AgentRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    system_prompt: str
    handoff_targets: list[str]
    is_default: bool
    created_at: datetime
    updated_at: datetime


class AgentRoleList(BaseModel):
    roles: list[AgentRoleRead]


# --- SwarmComposition ---------------------------------------------------

# Task types allowed by the daemon classifier (see
# syntexa.daemon.classifier.TASK_TYPE_KEYWORDS). Kept in sync here so the
# API rejects unknown types at the edge rather than after a DB round-trip.
VALID_TASK_TYPES: tuple[str, ...] = ("feature", "fix", "refactor", "security", "chore")


def _normalize_role_names(names: list[str]) -> list[str]:
    """Strip and lowercase each name; reject empty or non-slug entries.

    Compositions accept free-form role names, but the string still has to
    be a valid AgentRole slug because `_ensure_roles` materializes unknown
    names into agent_roles rows that must round-trip through the Roles API.
    """
    cleaned: list[str] = []
    for raw in names:
        name = (raw or "").strip()
        if not name:
            raise ValueError("role names cannot be empty")
        if not all(c.isalnum() or c in ("-", "_") for c in name):
            raise ValueError(
                f"role name '{raw}' must be alphanumeric with - or _"
            )
        cleaned.append(name.lower())
    return cleaned


class SwarmCompositionCreate(BaseModel):
    task_type: str = Field(..., min_length=1, max_length=32)
    roles: list[str] = Field(..., min_length=1)
    max_rounds: int = Field(default=60, ge=1, le=500)

    @field_validator("task_type")
    @classmethod
    def _task_type_is_known(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_TASK_TYPES:
            raise ValueError(
                f"task_type must be one of {VALID_TASK_TYPES}"
            )
        return v

    @field_validator("roles")
    @classmethod
    def _roles_are_slugs(cls, v: list[str]) -> list[str]:
        # Order matters (first role = entry point), but duplicates are
        # allowed — a composition can legitimately include two coders for
        # parallel work (see DEFAULT_COMPOSITIONS "refactor").
        return _normalize_role_names(v)


class SwarmCompositionUpdate(BaseModel):
    """Partial update. `task_type` is not mutable — it's the natural key
    that the daemon looks up by, and renaming would orphan defaults."""

    roles: list[str] | None = Field(default=None, min_length=1)
    max_rounds: int | None = Field(default=None, ge=1, le=500)

    @field_validator("roles")
    @classmethod
    def _roles_are_slugs(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        return _normalize_role_names(v)


class SwarmCompositionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: str
    roles: list[str]
    max_rounds: int
    created_at: datetime
    updated_at: datetime


class SwarmCompositionList(BaseModel):
    compositions: list[SwarmCompositionRead]


# --- SystemSettings ------------------------------------------------------

# System settings that can be updated at runtime
RUNTIME_SETTING_KEYS: set[str] = {
    "poll_interval",
    "max_concurrent",
    "log_retention_days",
    "agent_trigger_tag",
    "base_branch",
}

# Sensitive keys that should be masked in responses
SENSITIVE_SETTING_KEYS: set[str] = {
    "clickup_api_key",
    "github_token",
}


class SystemSettingItem(BaseModel):
    """A single setting key-value pair."""

    key: str
    value: Any
    updated_at: datetime


class SystemSettingUpdate(BaseModel):
    """Partial update for system settings.

    Only runtime-tunable settings can be updated.
    """

    poll_interval: int | None = Field(default=None, ge=10)
    max_concurrent: int | None = Field(default=None, ge=1)
    log_retention_days: int | None = Field(default=None, ge=1)
    agent_trigger_tag: str | None = Field(default=None, min_length=1)
    base_branch: str | None = Field(default=None, min_length=1)

    @field_validator("agent_trigger_tag", "base_branch")
    @classmethod
    def _strip_string(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip()
        return v


class SystemSettingsRead(BaseModel):
    """Full settings response including all tunable values."""

    poll_interval: int
    max_concurrent: int
    log_retention_days: int
    agent_trigger_tag: str
    base_branch: str
    repo_path: str


class ConnectionStatus(BaseModel):
    """Connection health status for external services."""

    service: str  # "clickup" or "github"
    status: str  # "connected", "error", "unconfigured"
    message: str | None = None


class SettingsStatusResponse(BaseModel):
    """Response for /settings/status endpoint."""

    connections: list[ConnectionStatus]


# --- SwarmInstance (Monitoring) ------------------------------------------

class SwarmInstanceRead(BaseModel):
    """A swarm instance for monitoring."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    task_name: str
    task_type: str
    branch: str
    status: str  # running / completed / failed / timeout
    active_agent: str | None
    pr_url: str | None
    started_at: datetime
    completed_at: datetime | None


class SwarmInstanceList(BaseModel):
    """List of swarm instances."""

    swarms: list[SwarmInstanceRead]


class SwarmLogResponse(BaseModel):
    """Conversation log for a completed swarm."""

    task_id: str
    task_name: str
    status: str
    log: str | None
    pr_url: str | None
    started_at: datetime
    completed_at: datetime | None


# --- LLMProvider ---------------------------------------------------------

# Provider types the backend knows how to wire into AG2. Keep in sync with
# syntexa.llm.provider_config.build_llm_config.
LLM_PROVIDER_TYPES: tuple[str, ...] = (
    "anthropic",
    "openai",
    "openrouter",
    "ollama",
    "openai_compatible",
)

# Provider types that don't require an api_key (local runtimes). Everything
# else must carry a key.
_NO_KEY_REQUIRED: set[str] = {"ollama"}


def _provider_name_is_slug(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("name cannot be empty")
    if not all(c.isalnum() or c in ("-", "_") for c in v):
        raise ValueError("name must be alphanumeric with - or _")
    return v.lower()


class LLMProviderCreate(BaseModel):
    """Register a new LLM provider.

    `api_key` is accepted here but never echoed back — responses expose only
    a masked preview. For providers that don't need auth (e.g. local Ollama),
    pass `null` or omit.
    """

    name: str = Field(..., min_length=1, max_length=64)
    provider_type: str = Field(..., min_length=1, max_length=32)
    base_url: str | None = Field(default=None, max_length=512)
    api_key: str | None = Field(default=None, max_length=2048)
    default_model: str = Field(..., min_length=1, max_length=128)
    is_active: bool = Field(default=True)

    @field_validator("name")
    @classmethod
    def _name_valid(cls, v: str) -> str:
        return _provider_name_is_slug(v)

    @field_validator("provider_type")
    @classmethod
    def _provider_type_known(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in LLM_PROVIDER_TYPES:
            raise ValueError(f"provider_type must be one of {LLM_PROVIDER_TYPES}")
        return v

    @model_validator(mode="after")
    def _key_required_when_applicable(self) -> "LLMProviderCreate":
        if self.provider_type not in _NO_KEY_REQUIRED and not self.api_key:
            raise ValueError(
                f"api_key is required for provider_type '{self.provider_type}'"
            )
        return self


class LLMProviderUpdate(BaseModel):
    """Partial update. Omit `api_key` to keep the stored one."""

    base_url: str | None = Field(default=None, max_length=512)
    api_key: str | None = Field(default=None, max_length=2048)
    default_model: str | None = Field(default=None, min_length=1, max_length=128)
    is_active: bool | None = None


class LLMProviderRead(BaseModel):
    """Response model — exposes a masked key preview only."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    provider_type: str
    base_url: str | None
    api_key_preview: str | None  # "sk-ant-…abcd" or None
    default_model: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LLMProviderList(BaseModel):
    providers: list[LLMProviderRead]


# --- Agent ---------------------------------------------------------------


class AgentCreate(BaseModel):
    """Create a new Agent.

    An Agent bundles a name, a system prompt, a provider (FK), and an
    optional model override. When `model` is NULL the agent inherits the
    provider's `default_model` at config-build time.
    """

    name: str = Field(..., min_length=1, max_length=64)
    system_prompt: str = Field(..., min_length=1)
    provider_id: int = Field(..., ge=1)
    model: str | None = Field(default=None, max_length=128)
    is_active: bool = Field(default=True)

    @field_validator("name")
    @classmethod
    def _name_valid(cls, v: str) -> str:
        return _provider_name_is_slug(v)


class AgentUpdate(BaseModel):
    """Partial update. `name` is intentionally NOT updatable — Swarms and
    other future wiring reference agents by name, and renaming would
    silently break those references. Users delete+recreate instead.
    """

    system_prompt: str | None = Field(default=None, min_length=1)
    provider_id: int | None = Field(default=None, ge=1)
    model: str | None = Field(default=None, max_length=128)
    is_active: bool | None = None


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    system_prompt: str
    provider_id: int
    model: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AgentList(BaseModel):
    agents: list[AgentRead]


# --- Repository ----------------------------------------------------------


class RepositoryCreate(BaseModel):
    """Register a new code repository.

    The `path` must be absolute but is NOT validated to exist on disk at
    schema-layer — rows can be pre-configured before the path is materialized.
    The /health endpoint surfaces disk reality.
    """

    name: str = Field(..., min_length=1, max_length=64)
    path: str = Field(..., min_length=1, max_length=1024)
    remote_url: str | None = Field(default=None, max_length=512)
    default_branch: str = Field(default="main", min_length=1, max_length=128)
    clickup_list_id: str | None = Field(default=None, max_length=64)
    is_active: bool = Field(default=True)

    @field_validator("name")
    @classmethod
    def _name_valid(cls, v: str) -> str:
        return _provider_name_is_slug(v)

    @field_validator("path")
    @classmethod
    def _path_non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("path cannot be empty")
        return v

    @field_validator("default_branch")
    @classmethod
    def _default_branch_stripped(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("default_branch cannot be empty")
        return v


class RepositoryUpdate(BaseModel):
    """Partial update.

    `name` is intentionally NOT updatable: other entities (e.g. Swarm in
    Phase 4) will reference repos by name, and renaming would silently
    break them — same justification as agent_roles / llm_providers. Users
    delete+recreate instead.
    """

    path: str | None = Field(default=None, min_length=1, max_length=1024)
    remote_url: str | None = Field(default=None, max_length=512)
    default_branch: str | None = Field(default=None, min_length=1, max_length=128)
    clickup_list_id: str | None = Field(default=None, max_length=64)
    is_active: bool | None = None

    @field_validator("path")
    @classmethod
    def _path_stripped(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("path cannot be empty")
        return v

    @field_validator("default_branch")
    @classmethod
    def _default_branch_stripped(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("default_branch cannot be empty")
        return v


class RepositoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    path: str
    remote_url: str | None
    default_branch: str
    clickup_list_id: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RepositoryList(BaseModel):
    repositories: list[RepositoryRead]


class RepositoryHealth(BaseModel):
    """Disk-reality check for a repository row.

    Read-only: no side effects. `default_branch_exists` is False if the
    path is not a git repo, if the branch is missing, or if the subprocess
    fails for any reason (including timeout).
    """

    is_git_repo: bool
    path_exists: bool
    default_branch_exists: bool


# --- Swarm ---------------------------------------------------------------

# Re-use the provider slug validator under a generic alias so new schemas
# don't have to reach into the LLMProvider block by name.
_is_slug = _provider_name_is_slug


ORCHESTRATOR_STRATEGIES: tuple[str, ...] = ("auto", "parallel", "sequential")
SWARM_STATUSES: tuple[str, ...] = ("idle", "running", "completed", "failed")


class SwarmCreate(BaseModel):
    """Create a first-class Swarm bound to a repository.

    `agent_ids` is a required non-empty ordered list. `manual_agent_order`
    is optional; when provided it must be a subset of `agent_ids` AND
    the orchestrator strategy must be "sequential".
    """

    name: str = Field(..., min_length=1, max_length=64)
    repository_id: int = Field(..., ge=1)
    task_description: str | None = Field(default=None)
    orchestrator_strategy: str = Field(default="auto", min_length=1, max_length=16)
    manual_agent_order: list[int] | None = None
    max_rounds: int = Field(default=60, ge=1, le=500)
    status: str = Field(default="idle", min_length=1, max_length=16)
    is_active: bool = Field(default=True)
    agent_ids: list[int] = Field(..., min_length=1)

    @field_validator("name")
    @classmethod
    def _name_valid(cls, v: str) -> str:
        return _is_slug(v)

    @field_validator("orchestrator_strategy")
    @classmethod
    def _strategy_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ORCHESTRATOR_STRATEGIES:
            raise ValueError(
                f"orchestrator_strategy must be one of {ORCHESTRATOR_STRATEGIES}"
            )
        return v

    @field_validator("status")
    @classmethod
    def _status_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in SWARM_STATUSES:
            raise ValueError(f"status must be one of {SWARM_STATUSES}")
        return v

    @field_validator("agent_ids")
    @classmethod
    def _agent_ids_unique(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("agent_ids must be unique")
        return v

    @model_validator(mode="after")
    def _manual_order_consistency(self) -> "SwarmCreate":
        if self.manual_agent_order is None:
            return self
        if self.orchestrator_strategy != "sequential":
            raise ValueError(
                "manual_agent_order is only valid when "
                "orchestrator_strategy='sequential'"
            )
        if len(self.manual_agent_order) != len(set(self.manual_agent_order)):
            raise ValueError("manual_agent_order must contain unique agent_ids")
        extras = set(self.manual_agent_order) - set(self.agent_ids)
        if extras:
            raise ValueError(
                f"manual_agent_order contains agent_ids not in agent_ids: {sorted(extras)}"
            )
        return self


class SwarmUpdate(BaseModel):
    """Partial update. `name` is intentionally NOT updatable — other rows
    (future orchestration state, logs) may reference swarms by name, so
    renaming would silently break them. Users delete+recreate instead.
    """

    repository_id: int | None = Field(default=None, ge=1)
    task_description: str | None = None
    orchestrator_strategy: str | None = Field(default=None, min_length=1, max_length=16)
    manual_agent_order: list[int] | None = None
    max_rounds: int | None = Field(default=None, ge=1, le=500)
    status: str | None = Field(default=None, min_length=1, max_length=16)
    is_active: bool | None = None
    agent_ids: list[int] | None = Field(default=None, min_length=1)

    @field_validator("orchestrator_strategy")
    @classmethod
    def _strategy_valid(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if v not in ORCHESTRATOR_STRATEGIES:
            raise ValueError(
                f"orchestrator_strategy must be one of {ORCHESTRATOR_STRATEGIES}"
            )
        return v

    @field_validator("status")
    @classmethod
    def _status_valid(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if v not in SWARM_STATUSES:
            raise ValueError(f"status must be one of {SWARM_STATUSES}")
        return v

    @field_validator("agent_ids")
    @classmethod
    def _agent_ids_unique(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None
        if len(v) != len(set(v)):
            raise ValueError("agent_ids must be unique")
        return v

    @model_validator(mode="after")
    def _manual_order_consistency(self) -> "SwarmUpdate":
        # If both strategy and manual_agent_order are being set in the same
        # payload, cross-check them; if only one side is provided, the route
        # layer does the full post-merge validation against DB state.
        if (
            self.manual_agent_order is not None
            and self.orchestrator_strategy is not None
            and self.orchestrator_strategy != "sequential"
        ):
            raise ValueError(
                "manual_agent_order is only valid when "
                "orchestrator_strategy='sequential'"
            )
        if self.manual_agent_order is not None:
            if len(self.manual_agent_order) != len(set(self.manual_agent_order)):
                raise ValueError(
                    "manual_agent_order must contain unique agent_ids"
                )
            if self.agent_ids is not None:
                extras = set(self.manual_agent_order) - set(self.agent_ids)
                if extras:
                    raise ValueError(
                        "manual_agent_order contains agent_ids not in agent_ids: "
                        f"{sorted(extras)}"
                    )
        return self


class SwarmRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    repository_id: int
    task_description: str | None
    orchestrator_strategy: str
    manual_agent_order: list[int] | None
    max_rounds: int
    status: str
    is_active: bool
    agents: list[AgentRead]
    created_at: datetime
    updated_at: datetime


class SwarmList(BaseModel):
    swarms: list[SwarmRead]


# --- ExternalCredentials --------------------------------------------------

class ExternalCredentialCreate(BaseModel):
    """Create a new external credential."""

    service_type: str = Field(..., min_length=1, max_length=32, description="Service type (clickup, github, etc.)")
    credentials: dict[str, Any] = Field(..., description="Service-specific credential fields")
    is_active: bool = Field(default=True)

    @field_validator("service_type")
    @classmethod
    def _service_type_is_valid(cls, v: str) -> str:
        v = v.strip().lower()
        allowed = {"clickup", "github", "jira", "linear", "gitlab", "custom"}
        if v not in allowed:
            raise ValueError(f"service_type must be one of: {allowed}")
        return v


class ExternalCredentialUpdate(BaseModel):
    """Update an existing external credential."""

    credentials: dict[str, Any] | None = None
    is_active: bool | None = None


class ExternalCredentialRead(BaseModel):
    """External credential for API responses (excludes sensitive data)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    service_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

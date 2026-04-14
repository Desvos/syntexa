"""Pydantic request/response schemas for the HTTP API.

Keep these separate from ORM entities: the DB stores handoff_targets as a
JSON-encoded string, but clients send/receive a real list[str]. The route
handlers do the translation.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    def _roles_non_empty(cls, v: list[str]) -> list[str]:
        # Order matters (first role = entry point), but duplicates are
        # allowed — a composition can legitimately include two coders for
        # parallel work (see DEFAULT_COMPOSITIONS "refactor").
        cleaned = [r.strip() for r in v]
        if any(not r for r in cleaned):
            raise ValueError("role names cannot be empty")
        return cleaned


class SwarmCompositionUpdate(BaseModel):
    """Partial update. `task_type` is not mutable — it's the natural key
    that the daemon looks up by, and renaming would orphan defaults."""

    roles: list[str] | None = Field(default=None, min_length=1)
    max_rounds: int | None = Field(default=None, ge=1, le=500)

    @field_validator("roles")
    @classmethod
    def _roles_non_empty(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        cleaned = [r.strip() for r in v]
        if any(not r for r in cleaned):
            raise ValueError("role names cannot be empty")
        return cleaned


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

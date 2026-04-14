# Implementation Plan: Agent Swarm Platform

**Spec**: [spec.md](spec.md)
**Status**: Draft
**Created**: 2026-04-14
**Author**: antoniodevivo

## Plan Overview

Syntexa is an autonomous coding platform built on AG2's swarm orchestration.
The implementation follows a layered architecture: adapter interfaces at the
edge, a daemon core in the middle, and a web dashboard for configuration and
monitoring. The first delivery focuses on the daemon with adapter-based
integrations (ClickUp, GitHub), followed by the dashboard for roles,
compositions, settings, and user management.

## Constitution Check

| Principle           | Status   | Notes |
|---------------------|----------|-------|
| Clarity First       | Aligned  | Each FR has unambiguous acceptance criteria; adapter interfaces are explicitly defined; role names are user-defined |
| Test-Driven         | Aligned  | Every phase includes a test strategy; swarm reliability is a tracked metric (80%+ target) |
| Modular Architecture | Aligned | Adapters decouple external services; roles are loosely coupled units; daemon, dashboard, and swarm engine are separate modules |
| Security by Default | Aligned | API keys in env vars; password hashing for users; workspaces isolated per task; no secrets in logs or PRs |

No concerns. Proceeding.

## Architecture Decisions

### AD-1: Python backend with AG2 swarm orchestration

**Context**: The system needs an agent framework that supports multi-agent
handoffs, shared context, and tool use. The existing prototype uses AG2.
**Decision**: Use Python as the backend language with AG2 as the swarm
orchestration framework.
**Alternatives Considered**: LangGraph (more complex graph model), CrewAI
(less flexible handoff control), custom orchestration (reinventing the wheel).
**Rationale**: AG2 provides native swarm handoffs, context variables, and
conditional routing. The existing prototype validates the approach. Python
ecosystem has mature HTTP, database, and task queue libraries. Constitution
alignment: Clarity First (AG2's swarm API is explicit and readable).

### AD-2: FastAPI for daemon API + dashboard backend

**Context**: The dashboard needs a web server that can serve both a REST API
and static frontend assets. The daemon needs an HTTP endpoint for status and
configuration.
**Decision**: Use FastAPI for the backend API. It provides async support,
automatic OpenAPI docs, and Pydantic validation.
**Alternatives Considered**: Flask (less async-friendly), Django (too heavy
for this scope), aiohttp (lower level, more boilerplate).
**Rationale**: FastAPI is lightweight, async-native, and generates API docs
automatically. Pydantic models align with Test-Driven principle (validation
built in). Constitution alignment: Clarity First (auto-generated docs make
the API self-documenting).

### AD-3: SQLite for persistence

**Context**: The system needs to persist user accounts, agent roles, swarm
compositions, settings, and swarm history. Single VPS deployment.
**Decision**: Use SQLite as the primary database.
**Alternatives Considered**: PostgreSQL (overkill for single-VPS), JSON files
(no query capability, no concurrency), Redis (volatile, not a primary store).
**Rationale**: SQLite requires no external service, handles concurrent reads
well, and is sufficient for a single-VPS deployment with 3-5 concurrent
swarms. Constitution alignment: Modular Architecture (easy to swap to
PostgreSQL later via adapter). Clarity First (single file, easy to inspect).

### AD-4: React frontend for dashboard

**Context**: The dashboard needs to manage agent roles, swarm compositions,
settings, user accounts, and view swarm status.
**Decision**: Use React with a lightweight component library for the
dashboard frontend.
**Alternatives Considered**: Vue.js (valid but smaller ecosystem), HTMX +
server-rendered (less interactive for real-time status), plain HTML/JS
(maintenance burden).
**Rationale**: React provides a mature ecosystem and component model suited
for forms, tables, and real-time status displays. Constitution alignment:
Clarity First (component structure is self-documenting).

### AD-5: Adapter pattern for external integrations

**Context**: Spec requires adapter architecture from the start for ClickUp
(project management) and GitHub (repository).
**Decision**: Define abstract base classes for ProjectManagementAdapter and
RepositoryAdapter. ClickUp and GitHub implement these interfaces.
**Alternatives Considered**: Direct API calls (violates spec requirement FR-13).
**Rationale**: Spec FR-13 mandates this. Constitution alignment: Modular
Architecture (new providers require only a new adapter, no core changes).

## Implementation Phases

### Phase 1: Daemon Core + Adapters

**Goal**: Deliver a working daemon that polls ClickUp, spawns AG2 swarms,
and creates GitHub PRs — all configurable via environment variables.
**Requirements Covered**: FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-11, FR-13

**Steps**:
1. Set up project structure (Python package, pyproject.toml, directory
   layout for daemon, adapters, models, api)
2. Define adapter interfaces (ProjectManagementAdapter, RepositoryAdapter)
3. Implement ClickUp adapter (list tasks, update status, add comment)
4. Implement GitHub adapter (create branch via worktree, commit, push, PR)
5. Implement config module (env var loading, validation, defaults)
6. Implement task polling and type detection (FR-1, FR-2)
7. Implement swarm assembly using AG2 (FR-3, FR-4) with default roles
8. Implement isolated workspace management (FR-5)
9. Implement PR delivery pipeline (FR-6)
10. Implement concurrency control with ThreadPoolExecutor (FR-11)
11. Implement log retention and cleanup (env-var configurable)
12. Add systemd service file for production deployment
13. Write integration tests for each adapter and the full daemon loop

**Deliverables**:
- `syntexa/` Python package with daemon, adapters, config, models
- ClickUp and GitHub adapter implementations
- AG2 swarm orchestration with default roles and compositions
- Test suite for adapters and daemon loop

**Test Strategy**:
- Unit tests for each adapter method (mocked API responses)
- Integration test: tag a task, verify swarm creates a branch and PR
- Concurrency test: submit multiple tasks, verify no more than max_concurrent
  run simultaneously

### Phase 2: Dashboard API + Data Model

**Goal**: Deliver the FastAPI backend with SQLite persistence for roles,
compositions, settings, users, and swarm history.
**Requirements Covered**: FR-7, FR-8, FR-9, FR-10, FR-12

**Steps**:
1. Define SQLAlchemy data models (User, AgentRole, SwarmComposition,
   SystemSettings, SwarmInstance)
2. Implement database migration setup (Alembic or manual schema)
3. Implement CRUD endpoints for agent roles (FR-7)
4. Implement CRUD endpoints for swarm compositions (FR-8)
5. Implement settings endpoints (FR-9) with live-reload support
6. Implement swarm monitoring endpoints (FR-10) — list active, list
   completed, get conversation log
7. Implement user management endpoints (FR-12) — login, create user,
   delete user, session handling
8. Implement log retention cleanup as a background task
9. Connect daemon to database for swarm instance tracking
10. Write API tests for each endpoint

**Deliverables**:
- FastAPI application with all CRUD endpoints
- SQLite schema with migrations
- Authentication middleware (session-based)
- API test suite

**Test Strategy**:
- Unit tests for each model and CRUD operation
- API endpoint tests (FastAPI TestClient)
- Auth tests: login, session expiry, unauthorized access

### Phase 3: Dashboard Frontend

**Goal**: Deliver the React dashboard for managing roles, compositions,
settings, users, and monitoring swarms.
**Requirements Covered**: FR-7, FR-8, FR-9, FR-10, FR-12 (UI layer)

**Steps**:
1. Scaffold React app with routing and layout shell
2. Build Login page with username/password form
3. Build Agent Roles management page (CRUD table + prompt editor)
4. Build Swarm Compositions page (drag-to-reorder role list per task type)
5. Build System Settings page (polling interval, max concurrent, retention)
6. Build Swarm Monitor page (active swarms, completed history, log viewer)
7. Build User Management page (create, delete users)
8. Add real-time polling for swarm status (refresh every N seconds)
9. End-to-end manual testing of all flows

**Deliverables**:
- React application with all dashboard pages
- API client layer communicating with FastAPI backend
- Responsive layout for desktop browsers

**Test Strategy**:
- Component tests for each page (React Testing Library)
- E2E test: login, create role, create composition, view swarm status
- Manual testing: full user journey from login to monitoring a completed swarm

## Dependencies & Risks

| Dependency / Risk | Impact | Mitigation |
|-------------------|--------|------------|
| AG2 API stability | Swarm orchestration breaks if AG2 changes | Pin AG2 version; monitor changelog |
| ClickUp API rate limits | Polling blocked if rate limit exceeded | Add exponential backoff; configurable poll interval |
| GitHub API token permissions | PR creation fails without correct scopes | Document required scopes; validate on startup |
| LLM provider downtime | Swarm stalls if model API is unreachable | Fallback chain (spec 002); graceful error handling |
| SQLite write contention | Database locks under high concurrency | WAL mode; single writer pattern via FastAPI |

## Open Questions

- LLM provider configuration is handled by spec 002 (llm-provider-settings)
  and will be integrated in a follow-up phase after both specs are implemented.
# Research: Agent Swarm Platform

## Decision 1: Agent Framework — AG2 (AutoGen)

**Chosen**: AG2 (ag2ai/ag2) v0.8+
**Rationale**: AG2 provides native swarm orchestration with SwarmAgent,
initiate_swarm_chat, ON_CONDITION, AFTER_WORK, and AfterWorkOption.
The existing prototype validates the approach. AG2 handles handoffs,
context_variables, and termination natively.
**Alternatives Considered**:
- LangGraph: More complex graph model, overkill for linear handoff chains
- CrewAI: Less flexible handoff control, higher abstraction cost
- Custom orchestration: Reinventing the wheel, violates Clarity First

## Decision 2: Backend Framework — FastAPI

**Chosen**: FastAPI with Uvicorn
**Rationale**: Async-native, automatic OpenAPI docs, Pydantic validation,
lightweight. Ideal for REST API + dashboard backend on a single VPS.
**Alternatives Considered**:
- Flask: No native async, would need gevent/celery
- Django: Overkill for this scope, batteries we don't need
- aiohttp: Lower level, more boilerplate

## Decision 3: Database — SQLite

**Chosen**: SQLite with WAL mode
**Rationale**: Zero-config, single-file, sufficient for single-VPS with
3-5 concurrent swarms. Easy to inspect and backup. Can migrate to
PostgreSQL later via adapter pattern (Constitution: Modular Architecture).
**Alternatives Considered**:
- PostgreSQL: Requires external service, overkill for VPS deployment
- JSON files: No query capability, no concurrency safety
- Redis: Not a primary data store

## Decision 4: Frontend — React

**Chosen**: React with Vite
**Rationale**: Mature ecosystem, component model fits dashboard forms/tables.
Vite provides fast dev server and optimized builds.
**Alternatives Considered**:
- Vue.js: Valid but smaller ecosystem for dashboard patterns
- HTMX + server-rendered: Less interactive for real-time status
- Plain HTML/JS: Maintenance burden

## Decision 5: Authentication — Session-based with bcrypt

**Chosen**: Session tokens stored in server-side cache, passwords hashed
with bcrypt.
**Rationale**: Simple, secure, fits single-VPS deployment. No JWT complexity
needed for superadmin-only auth.
**Alternatives Considered**:
- JWT: Overkill for single-app deployment, token revocation is harder
- OAuth2: No external identity provider needed
- Shared secret: No user management, violates FR-12

## Decision 6: Deployment — systemd

**Chosen**: systemd service for the daemon, reverse proxy (nginx/caddy)
for the dashboard.
**Rationale**: Standard Linux service management, auto-restart on failure,
log integration with journalctl. Existing prototype uses this pattern.
**Alternatives Considered**:
- Docker: Adds complexity for single-VPS, but viable future option
- Supervisor: Less standard than systemd on modern Linux
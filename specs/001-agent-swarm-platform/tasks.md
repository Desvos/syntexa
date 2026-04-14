# Task Breakdown: Agent Swarm Platform

**Plan**: [plan.md](plan.md)  
**Spec**: [spec.md](spec.md)  
**Data Model**: [data-model.md](data-model.md)  
**API Contracts**: [contracts/api.md](contracts/api.md)  
**Research**: [research.md](research.md)  
**Status**: Draft  
**Created**: 2026-04-14  
**Author**: antoniodevivo  

## Overview

This task breakdown follows the **User Story Phase** organization from the spec:
- **Phase 1**: Setup (project initialization)
- **Phase 2**: Foundational (blocking prerequisites - MUST complete before user stories)
- **Phase 3**: User Story 1 - Task Polling & Swarm Execution
- **Phase 4**: User Story 2 - Custom Agent Roles Management
- **Phase 5**: User Story 3 - Swarm Composition Management
- **Phase 6**: User Story 4 - System Settings & Monitoring
- **Phase 7**: User Story 5 - User Management
- **Phase 8**: Polish & Cross-Cutting Concerns

---

## Phase 1: Setup

**Goal**: Initialize project structure and core infrastructure

### Tasks

- [ ] T001 Create Python project structure with pyproject.toml in syntexa/
- [ ] T002 Create directory layout: syntexa/{daemon,adapters,models,api,config}
- [ ] T003 Set up pytest configuration and test directory structure
- [ ] T004 Add AG2 (autogen-agentchat>=0.8) dependency to pyproject.toml
- [ ] T005 Add FastAPI, Uvicorn, SQLAlchemy dependencies to pyproject.toml
- [ ] T006 Add bcrypt, python-dotenv, requests, httpx dependencies to pyproject.toml

---

## Phase 2: Foundational

**Goal**: Blocking prerequisites - database, adapters, and config MUST complete before user stories

### Tasks

- [x] T007 [P] Create SQLite database connection module in syntexa/models/database.py
- [x] T008 [P] Create SQLAlchemy models per data-model.md: User, AgentRole, SwarmComposition, SwarmInstance, SystemSettings
- [x] T009 Create database migration setup (Alembic configuration)
- [x] T010 [P] Define ProjectManagementAdapter abstract base class in syntexa/adapters/base.py
- [x] T011 [P] Define RepositoryAdapter abstract base class in syntexa/adapters/base.py
- [x] T012 [P] Implement config module for env var loading with validation in syntexa/config/settings.py
- [x] T013 Create systemd service file template in deploy/syntexa.service

---

## Phase 3: User Story 1 - Task Polling & Swarm Execution

**Story Goal**: Deliver a working daemon that polls ClickUp, spawns AG2 swarms, and creates GitHub PRs  
**Independent Test Criteria**: Tag a task in ClickUp, verify swarm creates a branch and PR within 30 minutes  
**Requirements**: FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-11, FR-13  
**Parallel Opportunities**: ClickUp and GitHub adapters can be developed in parallel

### Tasks

- [x] T014 [P] [US1] Implement ClickUp adapter list_tasks method in syntexa/adapters/clickup.py
- [x] T015 [P] [US1] Implement ClickUp adapter update_status method in syntexa/adapters/clickup.py
- [x] T016 [P] [US1] Implement ClickUp adapter add_comment method in syntexa/adapters/clickup.py
- [x] T017 [P] [US1] Implement GitHub adapter create_branch method in syntexa/adapters/github.py
- [x] T018 [P] [US1] Implement GitHub adapter commit method in syntexa/adapters/github.py
- [x] T019 [P] [US1] Implement GitHub adapter push method in syntexa/adapters/github.py
- [x] T020 [P] [US1] Implement GitHub adapter create_pr method in syntexa/adapters/github.py
- [x] T021 [P] [US1] Implement task polling loop in syntexa/daemon/poller.py
- [x] T022 [US1] Implement task type detection logic (feature/fix/refactor/security/chore) in syntexa/daemon/classifier.py
- [x] T023 [US1] Create default agent roles (planner, coder, tester, reviewer) in syntexa/daemon/roles.py
- [x] T024 [US1] Create default swarm compositions for each task type in syntexa/daemon/compositions.py
- [x] T025 [US1] Implement AG2 swarm assembly with handoff routing in syntexa/daemon/swarm.py
- [x] T026 [US1] Implement isolated workspace (branch) creation per task in syntexa/daemon/workspace.py
- [x] T027 [US1] Implement PR delivery pipeline in syntexa/daemon/delivery.py
- [x] T028 [US1] Implement concurrency control with ThreadPoolExecutor in syntexa/daemon/executor.py
- [x] T029 [US1] Integrate daemon components into main loop in syntexa/daemon/main.py
- [x] T030 [US1] Write unit tests for ClickUp adapter with mocked API responses
- [x] T031 [US1] Write unit tests for GitHub adapter with mocked API responses
- [x] T032 [US1] Write integration test for full daemon loop (tag → swarm → PR)
- [x] T033 [US1] Write concurrency test to verify max_concurrent enforcement

---

## Phase 4: User Story 2 - Custom Agent Roles Management

**Story Goal**: Users can create, edit, and delete custom agent roles via API and dashboard  
**Independent Test Criteria**: Create a custom role via API, use it in a swarm composition, verify swarm executes with new role  
**Requirements**: FR-7  
**Parallel Opportunities**: API endpoints and frontend pages can be developed in parallel after models exist

### Tasks

- [x] T034 [P] [US2] Create Pydantic schemas for AgentRole in syntexa/api/schemas.py
- [x] T035 [P] [US2] Implement GET /api/v1/roles endpoint in syntexa/api/routes/roles.py
- [x] T036 [P] [US2] Implement POST /api/v1/roles endpoint in syntexa/api/routes/roles.py
- [x] T037 [P] [US2] Implement PUT /api/v1/roles/{id} endpoint in syntexa/api/routes/roles.py
- [x] T038 [P] [US2] Implement DELETE /api/v1/roles/{id} endpoint in syntexa/api/routes/roles.py
- [x] T039 [US2] Write API tests for role CRUD endpoints
- [x] T040 [P] [US2] Build Agent Roles management page in dashboard/src/pages/Roles.jsx
- [x] T041 [P] [US2] Create role editor component with system prompt textarea in dashboard/src/components/RoleEditor.jsx
- [x] T042 [US2] Create handoff targets multi-select component in dashboard/src/components/HandoffTargets.jsx
- [x] T043 [US2] Build role table with CRUD actions in dashboard/src/components/RolesTable.jsx
- [x] T044 [US2] Write component tests for Roles page

---

## Phase 5: User Story 3 - Swarm Composition Management

**Story Goal**: Users can define which agent roles compose a swarm for each task type  
**Independent Test Criteria**: Create custom composition via dashboard, trigger task of that type, verify swarm uses custom composition  
**Requirements**: FR-8  
**Parallel Opportunities**: API and frontend can be developed in parallel after data model exists

### Tasks

- [x] T045 [P] [US3] Create Pydantic schemas for SwarmComposition in syntexa/api/schemas.py
- [x] T046 [P] [US3] Implement GET /api/v1/compositions endpoint in syntexa/api/routes/compositions.py
- [x] T047 [P] [US3] Implement POST /api/v1/compositions endpoint in syntexa/api/routes/compositions.py
- [x] T048 [P] [US3] Implement PUT /api/v1/compositions/{id} endpoint in syntexa/api/routes/compositions.py
- [x] T049 [P] [US3] Implement DELETE /api/v1/compositions/{id} endpoint in syntexa/api/routes/compositions.py
- [x] T050 [US3] Write API tests for composition CRUD endpoints
- [x] T051 [P] [US3] Build Swarm Compositions page in frontend/src/pages/Compositions.jsx
- [x] T052 [P] [US3] Create drag-to-reorder role list component in frontend/src/components/RoleOrder.jsx
- [x] T053 [US3] Create task type selector component in frontend/src/components/TaskTypeSelect.jsx
- [x] T054 [US3] Build composition table with edit/delete actions in frontend/src/components/CompositionsTable.jsx
- [x] T055 [US3] Write component tests for Compositions page

---

## Phase 6: User Story 4 - System Settings & Monitoring

**Story Goal**: Users can view and update system settings, monitor active and completed swarms  
**Independent Test Criteria**: Change polling interval via API, verify daemon picks up new interval; view active swarm status in dashboard  
**Requirements**: FR-9, FR-10  
**Parallel Opportunities**: Settings endpoints and monitoring endpoints can be developed in parallel

### Tasks

- [ ] T056 [P] [US4] Implement GET /api/v1/settings endpoint in syntexa/api/routes/settings.py
- [ ] T057 [P] [US4] Implement PATCH /api/v1/settings endpoint with live-reload support in syntexa/api/routes/settings.py
- [ ] T058 [P] [US4] Implement GET /api/v1/settings/status endpoint for connection health in syntexa/api/routes/settings.py
- [ ] T059 [US4] Implement settings change notification to daemon via file watcher or signal
- [ ] T060 [P] [US4] Implement GET /api/v1/swarms/active endpoint in syntexa/api/routes/swarms.py
- [ ] T061 [P] [US4] Implement GET /api/v1/swarms/completed endpoint with limit parameter in syntexa/api/routes/swarms.py
- [ ] T062 [P] [US4] Implement GET /api/v1/swarms/{id}/log endpoint in syntexa/api/routes/swarms.py
- [ ] T063 [US4] Implement log retention cleanup as background task in syntexa/daemon/cleanup.py
- [ ] T064 [US4] Write API tests for settings and monitoring endpoints
- [ ] T065 [P] [US4] Build System Settings page in dashboard/src/pages/Settings.jsx
- [ ] T066 [P] [US4] Build Swarm Monitor page in dashboard/src/pages/Monitor.jsx
- [ ] T067 [US4] Create active swarms list component with real-time polling in dashboard/src/components/ActiveSwarms.jsx
- [ ] T068 [US4] Create completed swarms history component in dashboard/src/components/CompletedSwarms.jsx
- [ ] T069 [US4] Create conversation log viewer component in dashboard/src/components/LogViewer.jsx
- [ ] T070 [US4] Create connection status indicator component in dashboard/src/components/ConnectionStatus.jsx
- [ ] T071 [US4] Write component tests for Settings and Monitor pages

---

## Phase 7: User Story 5 - User Management

**Story Goal**: Dashboard supports multiple user accounts with superadmin privileges  
**Independent Test Criteria**: Create user via API, log in with new user, verify superadmin access to all features  
**Requirements**: FR-12  
**Parallel Opportunities**: Auth endpoints and user management frontend can be developed in parallel

### Tasks

- [ ] T072 [P] [US5] Implement bcrypt password hashing utility in syntexa/api/auth.py
- [ ] T073 [P] [US5] Implement session token generation and validation in syntexa/api/auth.py
- [ ] T074 [P] [US5] Implement POST /api/v1/auth/login endpoint in syntexa/api/routes/auth.py
- [ ] T075 [P] [US5] Implement POST /api/v1/auth/logout endpoint in syntexa/api/routes/auth.py
- [ ] T076 [P] [US5] Implement GET /api/v1/users endpoint in syntexa/api/routes/users.py
- [ ] T077 [P] [US5] Implement POST /api/v1/users endpoint in syntexa/api/routes/users.py
- [ ] T078 [P] [US5] Implement DELETE /api/v1/users/{id} endpoint with self-delete protection in syntexa/api/routes/users.py
- [ ] T079 [US5] Implement authentication middleware for protected endpoints in syntexa/api/middleware.py
- [ ] T080 [US5] Write API tests for auth and user management endpoints
- [ ] T081 [P] [US5] Build Login page in dashboard/src/pages/Login.jsx
- [ ] T082 [P] [US5] Build User Management page in dashboard/src/pages/Users.jsx
- [ ] T083 [US5] Create login form component in dashboard/src/components/LoginForm.jsx
- [ ] T084 [US5] Create user table with create/delete actions in dashboard/src/components/UsersTable.jsx
- [ ] T085 [US5] Create protected route wrapper component in dashboard/src/components/ProtectedRoute.jsx
- [ ] T086 [US5] Implement session expiry handling in dashboard/src/utils/session.js
- [ ] T087 [US5] Write component tests for Login and Users pages

---

## Phase 8: Polish & Cross-Cutting Concerns

**Goal**: Final integration, documentation, and deployment readiness

### Tasks

- [x] T088 [P] Create main FastAPI application entry point in syntexa/api/main.py (pulled forward to Phase 4)
- [x] T089 [P] Set up React dashboard with Vite in dashboard/ (pulled forward to Phase 4)
- [ ] T090 [P] Create API client layer for dashboard in dashboard/src/api/client.js
- [ ] T091 [P] Create dashboard layout shell with navigation in dashboard/src/components/Layout.jsx
- [ ] T092 Implement dashboard routing with React Router in dashboard/src/App.jsx
- [ ] T093 Add responsive CSS/styling for desktop browsers in dashboard/src/styles/
- [ ] T094 Implement daemon-to-database integration for SwarmInstance tracking
- [ ] T095 Add error handling and logging throughout daemon and API
- [ ] T096 Write end-to-end test: login → create role → create composition → view swarm status
- [ ] T097 Write deployment documentation in docs/deployment.md
- [ ] T098 Create environment variable template in .env.example
- [ ] T099 Add API documentation generation with FastAPI auto-docs
- [ ] T100 Final integration testing and bug fixes

---

## Dependency Graph

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ├── T007-T009 (Database) ──────┐
    ├── T010-T011 (Adapters Base) ─┼──→ Phase 3 (US1: Task Polling & Swarm)
    └── T012-T013 (Config) ────────┘         └── All other phases depend on US1
    ↓
Phase 3 (US1) ─────────────────→ Phase 4,5,6,7,8 (can start after US1 daemon works)

Phase 4 (US2), 5 (US3), 6 (US4), 7 (US5) are INDEPENDENT after Phase 2 database
    └── Each has: API → Tests → Frontend → Component Tests
```

### User Story Completion Order

1. **US1 (Task Polling & Swarm Execution)** - MUST complete first (blocking)
2. **US2, US3, US4, US5** - Can be developed in parallel after Phase 2
3. **Phase 8** - Final integration after all user stories

---

## Parallel Execution Examples

### Within US1 (Task Polling & Swarm):
```
# Three developers can work in parallel:
Dev A: T014-T016 (ClickUp adapter)
Dev B: T017-T020 (GitHub adapter)
Dev C: T021-T029 (Daemon core + swarm)

# Then integrate:
All: T030-T033 (Tests)
```

### Across User Stories (after Phase 2):
```
# Four developers can work in parallel:
Dev A: US2 (Custom Agent Roles)
Dev B: US3 (Swarm Composition)
Dev C: US4 (Settings & Monitoring)
Dev D: US5 (User Management)
```

---

## Implementation Strategy

### MVP Scope

**User Story 1 ONLY** - A daemon that:
- Polls ClickUp for tagged tasks
- Spawns AG2 swarms with hardcoded default roles
- Creates GitHub PRs
- Runs via environment variables (no dashboard needed initially)

This delivers the core value proposition: autonomous coding from task tag to PR.

### Incremental Delivery

1. **Sprint 1**: Phase 1 + Phase 2 + US1 (daemon only, env vars)
2. **Sprint 2**: US2 + US3 (roles and compositions via API)
3. **Sprint 3**: US4 + US5 (settings, monitoring, users via API)
4. **Sprint 4**: Dashboard frontend for all features
5. **Sprint 5**: Polish, docs, deployment

### Critical Path

```
T001-T006 (Setup) → T007-T009 (Database) → T010-T013 (Adapters/Base) →
T014-T029 (US1 Core) → T088-T094 (Integration) → T100 (Final)
```

---

## Constitution Compliance Summary

| Principle | Tasks Tagged | Coverage |
|-----------|-------------|----------|
| Clarity First | All T001-T100 | Full - Every task has clear file paths and acceptance criteria |
| Test-Driven | T030-T033, T039, T050, T064, T080, T087, T096 | Partial - Test tasks explicitly defined; every implementation task should include tests |
| Modular Architecture | T010-T011, T014-T029, T034-T078 | Full - Adapter pattern, separate modules, clean interfaces |
| Security by Default | T072-T079, T085-T086 | Partial - Auth and session management covered |

---

## Task Count Summary

| Phase | Task Count | User Stories |
|-------|-----------|--------------|
| Phase 1: Setup | 6 | — |
| Phase 2: Foundational | 7 | — |
| Phase 3: US1 | 20 | Task Polling & Swarm Execution |
| Phase 4: US2 | 11 | Custom Agent Roles |
| Phase 5: US3 | 11 | Swarm Composition |
| Phase 6: US4 | 16 | Settings & Monitoring |
| Phase 7: US5 | 16 | User Management |
| Phase 8: Polish | 13 | — |
| **Total** | **100** | **5 User Stories** |

---

## Suggested MVP Tasks (US1 Only)

If delivering incrementally, prioritize these 20 tasks from US1:
- T001-T006: Setup
- T007-T013: Foundational
- T014-T029: Core daemon implementation
- T030-T033: Core tests

This delivers a working daemon that can be deployed and tested end-to-end before building the dashboard.

# Code map

A file-by-file index of what lives where. Pair with
[ARCHITECTURE.md](./ARCHITECTURE.md) when you need to navigate to the
right module quickly. Paths are relative to the repo root.

## Backend — `backend/syntexa/`

### Entry points

| File | Purpose |
|---|---|
| `api/main.py` | FastAPI app factory, router registration, `syntexa-api` console script, lifespan hook that calls `init_engine()` |
| `daemon/main.py` | `syntexa-daemon` console script; resolves credentials, starts the listener registry, handles SIGINT/SIGTERM |
| `pyproject.toml` | Console script declarations, dependencies, pytest config |
| `alembic.ini` | Alembic config (migration directory, URL template) |

### `api/` — HTTP layer

| File | Purpose |
|---|---|
| `api/main.py` | `create_app()`, includes each router under `/api/v1`, health route, `run()` uvicorn runner |
| `api/auth.py` | bcrypt helpers, session-token table in `sessions.db`, `create_session` / `get_session` / `delete_session` |
| `api/middleware.py` | `require_auth` FastAPI dependency — parses bearer token, looks up session, returns `SessionData` or 401 |
| `api/dependencies.py` | `get_db_session()` — yields a SQLAlchemy session per request |
| `api/schemas.py` | All Pydantic request/response models (one place for the API surface) |

### `api/routes/` — one module per resource

| File | Prefix | Notable endpoints |
|---|---|---|
| `routes/auth.py` | `/auth` | `POST /login`, `POST /logout`, `GET /me`, `POST /signup` |
| `routes/users.py` | `/users` | `GET`, `POST`, `DELETE` |
| `routes/settings.py` | `/settings` | `GET`, `PATCH`, `GET /status` |
| `routes/llm_providers.py` | `/llm-providers` | CRUD; response masks `api_key` |
| `routes/agents.py` | `/agents` | CRUD; RESTRICTed delete if agent is in a swarm |
| `routes/repositories.py` | `/repositories` | CRUD + `GET /{id}/health` (path/git/branch checks) |
| `routes/swarms.py` | `/swarms` | CRUD + `POST /{id}/run` (synchronous orchestrator call) |
| `routes/credentials.py` | `/credentials` | External service credentials (ClickUp, GitHub, …) |
| `routes/listeners.py` | `/listeners` | `GET` status, `POST /{source}/start|stop` |
| `routes/presets.py` | `/presets` | Read built-in catalogs + `POST /apply` to seed |

### `models/` — persistence

| File | Purpose |
|---|---|
| `models/database.py` | `init_engine`, `get_session_factory`, `session_scope`, `get_db_session`, `create_all` (tests only) |
| `models/entities.py` | Every SQLAlchemy model: User, SystemSetting, LLMProvider, Agent, Repository, Swarm, SwarmAgent, ExternalCredential, ProcessedEvent |
| `models/__init__.py` | Re-exports models |

### `config/` and `core/`

| File | Purpose |
|---|---|
| `config/settings.py` | Pydantic `Settings`, `env_prefix="SYNTEXA_"`, `get_settings()` (cached) |
| `core/crypto.py` | Fernet init (`SYNTEXA_ENCRYPTION_KEY` or `~/.syntexa/encryption.key`), `encrypt()`, `decrypt()`, `mask_key()` |

### `orchestrator/`

| File | Purpose |
|---|---|
| `orchestrator/executor.py` | `run_swarm(swarm_id, ...)`, `_load_swarm_bundle`, `_pick_meta_provider`, `_run_parallel`, `_run_sequential`, `_default_agent_runner` (AG2 bridge) |
| `orchestrator/decision.py` | `decide_strategy()` — auto/sequential/parallel picker, LLM meta-agent JSON parsing |
| `orchestrator/__init__.py` | Public API: `Orchestrator`, `OrchestratorResult` |

### `llm/`

| File | Purpose |
|---|---|
| `llm/provider_config.py` | `build_llm_config(provider, model=None)` — maps provider_type → AG2 `config_list`; decrypts API key; `mask_key()` for UI previews |

### `listeners/`

| File | Purpose |
|---|---|
| `listeners/base.py` | `Listener` ABC, `_run_loop` with exponential backoff, `start/stop` lifecycle |
| `listeners/event.py` | `InboundEvent` dataclass (source, external_id, payload) |
| `listeners/clickup_listener.py` | Polls ClickUp list for tagged tasks, spawns swarms, writes `ProcessedEvent` |
| `listeners/telegram_listener.py` | Telegram bot-updates listener, parses `repo:<slug>` prefix |
| `listeners/registry.py` | Module-level registry: `start_listener`, `stop_listener`, `start_all`, `stop_all`, `status` |

### `adapters/`

| File | Purpose |
|---|---|
| `adapters/base.py` | `ProjectManagementAdapter` and `RepositoryAdapter` ABCs; `NoOp*` fallbacks |
| `adapters/clickup.py` | ClickUp REST client (list tasks by tag, update status, add comment) |
| `adapters/github.py` | GitHub REST client (branches, commits, PRs) |

### `daemon/`

The daemon is the standalone process for listener-driven operation. Some
modules inside carry historical names from the pre-simple-swarms era;
the legacy DB tables were dropped in migration
`9c4f2a8e7b13_drop_legacy_agent_roles_compositions_instances.py`.

| File | Purpose |
|---|---|
| `daemon/main.py` | Entry: init logging + engine, resolve creds, build adapters, register signal handlers, enter poller loop |
| `daemon/poller.py` | Main polling cycle — invokes `PM adapter.list_tasks` and dispatches to the executor |
| `daemon/executor.py` | `SwarmExecutor` — `ThreadPoolExecutor` capped by `max_concurrent` |
| `daemon/swarm.py` | `SwarmEngine` interface + concrete AG2 implementation |
| `daemon/workspace.py` | Worktree creation/cleanup per task |
| `daemon/delivery.py` | Post-run delivery (PM status update, PR creation) |
| `daemon/classifier.py` | Task-type classification (feature/fix/refactor/…) |
| `daemon/settings_watcher.py` | Reloads runtime settings from DB |

### `presets/`

| File | Purpose |
|---|---|
| `presets/agents.py` | `BUILTIN_AGENT_PRESETS` — planner, coder, reviewer, tester, doc-writer, debugger |
| `presets/providers.py` | `BUILTIN_PROVIDER_PRESETS` — templates for Anthropic/OpenAI/OpenRouter/Ollama |
| `presets/swarm_templates.py` | `BUILTIN_SWARM_TEMPLATES` — quick-fix, feature-dev, review-only, auto |
| `presets/apply.py` | `apply_preset(kind, preset_name, overrides)` — seeds the DB |

### `migrations/versions/`

Eight revisions. Latest (head) drops the legacy schema:

1. `086673a46198_initial_schema` — users, system_settings, (legacy) agent_roles/swarm_compositions/swarm_instances
2. `3b87d5d313c7_add_agents_table` — agents + FK to llm_providers
3. `d46ac74852ca_add_llm_providers_table` — llm_providers
4. `3a0397047483_add_repositories_table` — repositories
5. `171d57f353b4_add_swarms_tables` — swarms + swarm_agents join
6. `f544d974925d_add_external_credentials_table`
7. `8b2e9a37c1d4_add_processed_events_and_trigger_tag` — dedupe table + `clickup_trigger_tag`
8. `9c4f2a8e7b13_drop_legacy_agent_roles_compositions_instances` — removes pre-refactor tables

### `tests/`

| File | Purpose |
|---|---|
| `tests/conftest.py` | Fixtures: `test_db_path`, `db_session`, `client`, `auth_headers` |
| `tests/test_agents_api.py` | Agent CRUD |
| `tests/test_auth_api.py` | Login/logout + session expiry |
| `tests/test_crypto.py` | Fernet roundtrip |
| `tests/test_clickup_adapter.py` | ClickUp REST adapter |
| `tests/test_clickup_listener.py` | Polling + dedupe behavior |
| `tests/test_executor.py` | Daemon thread-pool executor |
| `tests/test_orchestrator_decision.py` | Strategy picker + LLM JSON parsing |
| `tests/test_orchestrator_executor.py` | `run_swarm` with stubbed agents |
| `tests/test_llm_provider_config.py` | `build_llm_config` per provider type |
| `tests/test_repositories_api.py` | Repo CRUD + health |
| `tests/test_swarms_api.py` | Swarm CRUD + `/run` |
| `tests/test_listeners_api.py` | Listener start/stop/status |
| `tests/test_settings_api.py` | Settings CRUD |

## Frontend — `frontend/src/`

### Entry points

| File | Purpose |
|---|---|
| `index.html` | HTML shell; mounts `<div id="root">` |
| `src/main.jsx` | React root; `ThemeContextProvider` → `BrowserRouter` → `<App>` with 8 routes; wires auth error + session-expiry handlers |
| `vite.config.js` | Dev server on `:5173`; proxies `/api/*` and `/health/*` to `http://127.0.0.1:8000`; Vitest (jsdom) config |
| `package.json` | Dependencies (React 18, MUI 9, react-router 6, MUI X DataGrid); scripts |

### `src/api/`

| File | Purpose |
|---|---|
| `api/client.js` | `request(path, opts)` fetch wrapper; `ApiError` class; 401 interceptor (logout + redirect); `api.*` namespaces for every backend route |
| `api/auth.js` | `getToken/setToken/removeToken`, `isAuthenticated`, `authApi.login/logout`, session-expiry timer helpers |

### `src/components/` — reusable UI

| File | Purpose |
|---|---|
| `AppLayout.jsx` | Shell: 264px desktop sidebar / mobile drawer, AppBar with page title |
| `ProtectedRoute.jsx` | Auth guard; redirects to `/login` if no token |
| `ThemeContextProvider.jsx` | Light/dark mode context + localStorage persistence; wraps `<CssBaseline>` |
| `LoginForm.jsx` | Username/password form with visibility toggle and loading state |
| `UserMenu.jsx` | AppBar dropdown — theme toggle + logout |
| `UsersTable.jsx` | MUI X DataGrid for users with delete action |
| `ConnectionStatus.jsx` | Service-status card (ClickUp, DB, …) with color-coded chips |
| `LoadingFallback.jsx` | Skeleton/spinner during lazy loads |

### `src/pages/` — one component per route

| File | Route | Purpose |
|---|---|---|
| `Login.jsx` | `/login` | Full-screen login with gradient backdrop |
| `Wizard.jsx` | `/` | 3-step stepper: repo → task → agents; inline run-result card (largest page, ~700 lines) |
| `Swarms.jsx` | `/swarms` | Swarm table; run/details/delete; inline `RunResultInline` |
| `Agents.jsx` | `/agents` | Agent CRUD; provider selector |
| `LLMProviders.jsx` | `/llm-providers` | Provider CRUD; API keys never prefilled; shows last-4 preview |
| `Repositories.jsx` | `/repositories` | Repo CRUD; per-row health check (git/path/branch) |
| `Users.jsx` | `/users` | User admin; self-delete guard |
| `Settings.jsx` | `/settings` | Runtime settings sliders + `ConnectionStatus` side card |

### `src/theme.js`, `src/styles/`

| File | Purpose |
|---|---|
| `theme.js` | Brand tokens (indigo + teal), light/dark palettes, component overrides (Button, Card, AppBar backdrop-blur, DataGrid, Dialog, Scrollbar) |
| `styles/base.css` | Global `prefers-reduced-motion` rule; `color-scheme: light dark` |

## Root directories outside `backend/` and `frontend/`

### `deploy/`

| File | Purpose |
|---|---|
| `syntexa.service` | systemd unit for `syntexa-daemon`, user `syntexa`, env file `/etc/syntexa/syntexa.env`, hardening flags (`NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict`) |

No Docker, compose, or Kubernetes configs exist — systemd is the only
production template.

### `scripts/` (root)

| File | Purpose |
|---|---|
| `dev.sh` | Bash dev launcher (`api`/`daemon`/`frontend`/`all`); autodetects venv path |
| `dev.py` | Python cross-platform launcher |
| `dev.bat` | Windows batch launcher; opens separate cmd windows per service |

`backend/scripts/` exists but is empty.

### `specs/`

Spec-kit artifacts. Four features have folders:

| Folder | Status | What it covers |
|---|---|---|
| `001-agent-swarm-platform/` | In progress (Phases 1–8 defined; core implemented) | The whole platform — daemon, adapters, API, auth |
| `002-llm-provider-settings/` | Draft | Dashboard UI for provider selection |
| `003-orchestrators-monitoring/` | Draft | Real-time swarm monitoring |
| `004-frontend-mui-refactor/` | In progress | Incremental migration to MUI v6 |

Each folder has `spec.md` (functional requirements) and typically `plan.md` (phase decomposition) + `tasks.md` (checkbox task list).

### `graphify-out/`

Generated knowledge-graph artifacts. See
`graphify-out/GRAPH_REPORT.md` for the corpus overview. Regenerate
after large changes with the watch command in the project CLAUDE.md.

### `tmp/`

Gitignored scratch. Currently holds `ag2-coding-daemon/`, the
predecessor reference implementation. Safe to ignore.

### Root files

| File | Purpose |
|---|---|
| `README.md` | User-facing overview + local dev quickstart |
| `CLAUDE.md` | Project instructions for the Claude Code harness (graphify rules, spec-kit workflow, `bun`-only rule) |
| `skills-lock.json` | Pinned agent skills (find-skills, python-design-patterns, vercel-react-best-practices) |
| `.gitignore` | Tracks source + specs + deploy; ignores `__pycache__`, `node_modules`, `*.db`, `worktrees/`, `.env*`, `graphify*`, `tmp/` |

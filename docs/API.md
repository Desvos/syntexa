# API reference

All endpoints are prefixed with `/api/v1`. Everything except the auth
routes requires a bearer token issued by `POST /auth/login`.

## Auth

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/auth/signup` | Create a new user. |
| `POST` | `/auth/login` | Exchange credentials for a session token. |
| `POST` | `/auth/logout` | Invalidate the caller's session. |
| `GET`  | `/auth/me` | Return the current user. |

## Users

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/users` | List users. |
| `DELETE` | `/users/{id}` | Delete a user. |

## Settings

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/settings` | Read runtime settings. |
| `PATCH` | `/settings` | Update runtime-tunable settings. |
| `GET` | `/settings/status` | External connection health. |

## LLM providers

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/llm-providers` | List providers (keys masked). |
| `POST` | `/llm-providers` | Register a provider + encrypted key. |
| `PUT` | `/llm-providers/{id}` | Update fields (rotate key, change model). |
| `DELETE` | `/llm-providers/{id}` | Remove a provider. |

## Agents

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/agents` | List agents. |
| `POST` | `/agents` | Create a custom agent. |
| `PUT` | `/agents/{id}` | Update prompt / provider / model. |
| `DELETE` | `/agents/{id}` | Delete an agent (RESTRICT if still in a swarm). |

## Repositories

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/repositories` | List repositories. |
| `POST` | `/repositories` | Register a repo. |
| `PUT` | `/repositories/{id}` | Update path / branch / tag. |
| `DELETE` | `/repositories/{id}` | Remove a repo. |
| `GET` | `/repositories/{id}/health` | Disk-reality check. |

## Swarms

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/swarms` | List swarms. Optional `?repository_id` + `?status`. |
| `POST` | `/swarms` | Create a swarm. |
| `GET` | `/swarms/{id}` | Read one swarm. |
| `PATCH` | `/swarms/{id}` | Update fields / replace agent membership. |
| `DELETE` | `/swarms/{id}` | Delete a swarm. |
| `POST` | `/swarms/{id}/run` | Invoke the orchestrator synchronously. |

## Listeners

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/listeners` | List configured listeners + their status. |
| `POST` | `/listeners/{source}/start` | Start a listener (source = clickup/telegram). |
| `POST` | `/listeners/{source}/stop` | Stop a listener. |

## External credentials

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/credentials` | List external-service credentials. |
| `POST` | `/credentials` | Store a new credential (encrypted). |
| `PUT` | `/credentials/{id}` | Update an existing credential. |
| `DELETE` | `/credentials/{id}` | Remove a credential. |

## Presets (Phase 9)

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/presets/agents` | List built-in agent presets. |
| `GET` | `/presets/providers` | List built-in provider templates. |
| `GET` | `/presets/swarm-templates` | List swarm blueprints. |
| `POST` | `/presets/apply` | Seed a preset into the DB. |

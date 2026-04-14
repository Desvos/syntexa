# API Contracts: Agent Swarm Platform

Base URL: `/api/v1`

## Authentication

All endpoints require session cookie (except `POST /auth/login`).

## Auth

### POST /auth/login
Request: `{ "username": "string", "password": "string" }`
Response 200: `{ "user": { "id", "username" } }` + Set-Cookie: session
Response 401: `{ "error": "Invalid credentials" }`

### POST /auth/logout
Response 200: `{ "message": "Logged out" }`

## Users

### GET /users
Response 200: `{ "users": [{ "id", "username", "created_at", "last_login_at" }] }`

### POST /users
Request: `{ "username": "string", "password": "string" }`
Response 201: `{ "user": { "id", "username", "created_at" } }`

### DELETE /users/{id}
Response 204: No content
Response 403: Cannot delete own account

## Agent Roles

### GET /roles
Response 200: `{ "roles": [{ "id", "name", "system_prompt", "handoff_targets", "is_default", "created_at", "updated_at" }] }`

### POST /roles
Request: `{ "name": "string", "system_prompt": "string", "handoff_targets": ["string"] }`
Response 201: `{ "role": { ... } }`

### PUT /roles/{id}
Request: `{ "system_prompt"?: "string", "handoff_targets"?: ["string"] }`
Response 200: `{ "role": { ... } }`

### DELETE /roles/{id}
Response 204 / 409 (if role is in use)

## Swarm Compositions

### GET /compositions
Response 200: `{ "compositions": [{ "id", "task_type", "roles", "max_rounds" }] }`

### POST /compositions
Request: `{ "task_type": "string", "roles": ["string"], "max_rounds"?: number }`
Response 201: `{ "composition": { ... } }`

### PUT /compositions/{id}
Request: `{ "roles"?: ["string"], "max_rounds"?: number }`
Response 200: `{ "composition": { ... } }`

### DELETE /compositions/{id}
Response 204

## System Settings

### GET /settings
Response 200: `{ "settings": { "poll_interval": number, "max_concurrent": number, "log_retention_days": number, ... } }`

### PATCH /settings
Request: `{ "poll_interval"?: number, "max_concurrent"?: number, ... }`
Response 200: `{ "settings": { ... } }`

### GET /settings/status
Response 200: `{ "clickup": "connected" | "error", "github": "connected" | "error" }`

## Swarm Monitoring

### GET /swarms/active
Response 200: `{ "swarms": [{ "id", "task_id", "task_name", "active_agent", "started_at" }] }`

### GET /swarms/completed
Query params: `?limit=50`
Response 200: `{ "swarms": [{ "id", "task_id", "task_name", "status", "pr_url", "completed_at" }] }`

### GET /swarms/{id}/log
Response 200: `{ "log": "string (full conversation)" }`

## Health

### GET /health
Response 200: `{ "status": "ok", "version": "string" }`
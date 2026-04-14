# Data Model: Agent Swarm Platform

## Entities

### User
| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PK, AUTOINCREMENT | |
| username | VARCHAR(64) | UNIQUE, NOT NULL | |
| password_hash | VARCHAR(256) | NOT NULL | bcrypt hash |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | |
| last_login_at | DATETIME | NULL | Updated on login |

### AgentRole
| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PK, AUTOINCREMENT | |
| name | VARCHAR(64) | UNIQUE, NOT NULL | e.g. "planner", "coder" |
| system_prompt | TEXT | NOT NULL | Agent's instruction |
| handoff_targets | TEXT | NOT NULL | JSON array of role names |
| is_default | BOOLEAN | NOT NULL, DEFAULT FALSE | Default roles cannot be deleted |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | |
| updated_at | DATETIME | NOT NULL | |

### SwarmComposition
| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PK, AUTOINCREMENT | |
| task_type | VARCHAR(32) | UNIQUE, NOT NULL | e.g. "feature", "fix" |
| roles | TEXT | NOT NULL | JSON ordered array of role names |
| max_rounds | INTEGER | NOT NULL, DEFAULT 60 | Max conversation turns |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | |
| updated_at | DATETIME | NOT NULL | |

### SwarmInstance
| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PK, AUTOINCREMENT | |
| task_id | VARCHAR(32) | NOT NULL, UNIQUE | External task ID |
| task_name | VARCHAR(256) | NOT NULL | |
| task_type | VARCHAR(32) | NOT NULL | |
| branch | VARCHAR(128) | NOT NULL | Git branch name |
| status | VARCHAR(16) | NOT NULL | running / completed / failed / timeout |
| active_agent | VARCHAR(64) | NULL | Current agent role name |
| conversation_log | TEXT | NULL | Full swarm conversation |
| pr_url | VARCHAR(512) | NULL | PR link after completion |
| started_at | DATETIME | NOT NULL | |
| completed_at | DATETIME | NULL | |

### SystemSettings
| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| key | VARCHAR(64) | PK | |
| value | TEXT | NOT NULL | JSON-encoded value |
| updated_at | DATETIME | NOT NULL | |

Pre-populated keys: poll_interval, max_concurrent, log_retention_days,
repo_path, base_branch, clickup_api_key, github_token, github_owner,
github_repo, agent_trigger_tag

## Relationships

- SwarmComposition.roles references AgentRole.name (loose ref, enforced at app level)
- SwarmInstance.task_type references SwarmComposition.task_type
- SwarmInstance.active_agent references AgentRole.name

## State Transitions

### SwarmInstance.status
```
running → completed | failed | timeout
```
- `running`: Swarm is actively processing
- `completed`: PR created successfully
- `failed`: Error occurred, task status reverted
- `timeout`: Exceeded max_rounds

## Indexes

- User.username (UNIQUE)
- AgentRole.name (UNIQUE)
- SwarmComposition.task_type (UNIQUE)
- SwarmInstance.task_id (UNIQUE)
- SwarmInstance.status (for active queries)
- SwarmInstance.completed_at (for retention cleanup)
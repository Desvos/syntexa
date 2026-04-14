# Feature Specification: LLM Provider Settings

**Short Name**: llm-provider-settings
**Status**: Draft
**Created**: 2026-04-14
**Author**: antoniodevivo

## Overview

This feature gives platform administrators the ability to configure
which language model provider the agent swarm uses, directly from the
web dashboard. Administrators can choose between multiple providers
(such as direct provider access, aggregator services, or self-hosted
runtimes), set credentials, assign models per provider, and control
which provider each agent role uses. This eliminates the need to edit
configuration files or restart the daemon to change provider settings.

## User Scenarios & Testing

### Primary Scenario

**As a** platform administrator,
**I want** to select and configure the language model provider for each
agent role through the dashboard,
**So that** I can control costs, switch providers without downtime, and
assign the best model for each task.

**Steps**:
1. Administrator opens the dashboard settings page
2. Administrator selects a provider (e.g., direct, aggregator, or
   self-hosted) from the provider list
3. Administrator enters the required credentials for that provider
4. Administrator selects which model each agent role should use
5. Administrator saves the configuration
6. New swarm tasks immediately use the updated provider and model
   settings

### Alternative Scenarios

| Scenario                     | Condition                            | Expected Outcome                         |
|------------------------------|--------------------------------------|------------------------------------------|
| Switch primary provider      | Administrator changes the default    | New tasks use the new provider; running  |
|                              | provider                             | swarms continue with old settings        |
| Use self-hosted provider     | Administrator selects a self-hosted  | System connects to local endpoint; no    |
|                              | option                               | external API calls are made              |
| Add fallback provider        | Administrator configures a second    | If primary provider fails, the system    |
|                              | provider as fallback                 | automatically retries with the fallback   |
| Per-role model override      | Administrator assigns a specific     | That role uses the specified              |
|                              | model to the "reviewer" role          | provider/model instead of the default    |
| Invalid credentials           | Administrator enters wrong API key   | System validates and shows an error;      |
|                              |                                      | configuration is not saved               |
| Provider endpoint unreachable| Self-hosted endpoint is down         | System logs the error and falls back to   |
|                              |                                      | the next configured provider             |

### Edge Cases

| Edge Case                    | Trigger                            | Handling                                |
|------------------------------|------------------------------------|-----------------------------------------|
| Credentials rotation         | API key expires mid-swarm          | Running swarms may fail; new swarms use |
|                              |                                    | updated credentials from next config    |
| Empty provider list          | No providers configured            | System rejects configuration save and   |
|                              |                                    | shows validation error                  |
| Duplicate provider entries   | Same provider added twice          | System rejects the duplicate and shows  |
|                              |                                    | a warning                               |
| Self-hosted provider slow    | Response times exceed threshold    | System records latency metric;          |
| response                     |                                    | administrator is alerted via dashboard  |
| Simultaneous config edits    | Two admins save at the same time   | Last-write-wins with timestamp;         |
|                              |                                    | dashboard shows last-updated timestamp  |

## Functional Requirements

### FR-1: Provider Configuration

**Priority**: Must
**Description**: The dashboard MUST allow administrators to add,
edit, and remove language model providers. Each provider entry
includes a display name, provider type, endpoint URL, and
authentication credentials.

**Acceptance Criteria**:
- [ ] Administrators can add a new provider by selecting its type and
  entering required connection details
- [ ] Administrators can edit an existing provider's name, endpoint,
  and credentials
- [ ] Administrators can delete a provider that is not currently
  assigned to any agent role (with confirmation)
- [ ] Provider credentials are stored securely and never displayed in
  full after initial entry

### FR-2: Provider Types

**Priority**: Must
**Description**: The system MUST support at least three provider
types: direct provider access, aggregator service, and self-hosted
runtime. Each type has different connection requirements.

**Acceptance Criteria**:
- [ ] Direct provider type requires an API key and accepts a default
  model name
- [ ] Aggregator service type requires an API key, endpoint URL, and
  accepts a default model name
- [ ] Self-hosted type requires an endpoint URL only (no API key) and
  accepts a default model name
- [ ] The provider type determines which fields are required and which
  are optional

### FR-3: Model Selection per Provider

**Priority**: Must
**Description**: Each provider MUST support one or more model
identifiers. Administrators can select which model to use as the
default for that provider.

**Acceptance Criteria**:
- [ ] Each provider configuration includes a default model field
- [ ] The model field accepts a free-text identifier (no hardcoded
  model list)
- [ ] A validation check confirms the model is reachable through the
  provider before saving

### FR-4: Per-Role Model Assignment

**Priority**: Must
**Description**: Administrators MUST be able to assign a specific
provider and model to each agent role, overriding the global default.
If no per-role assignment is made, the role uses the global default.

**Acceptance Criteria**:
- [ ] Each agent role has a "model assignment" section in the role
  editor
- [ ] Administrators can select any configured provider and model for
  a role
- [ ] Unassigned roles inherit the global default provider and model
- [ ] Changing the global default does not override per-role
  assignments

### FR-5: Credential Validation

**Priority**: Must
**Description**: The system MUST validate provider credentials before
saving them. Invalid credentials are rejected with a clear error
message.

**Acceptance Criteria**:
- [ ] A test connection is attempted when credentials are saved
- [ ] If the connection fails, a descriptive error is shown and the
  configuration is not saved
- [ ] If the connection succeeds, the credentials are stored and the
  provider status is set to "connected"
- [ ] Validation runs in the background and does not block the
  dashboard for more than 10 seconds

### FR-6: Fallback Chain

**Priority**: Should
**Description**: Administrators SHOULD be able to configure an
ordered list of fallback providers. If the primary provider fails,
the system tries the next provider in the chain.

**Acceptance Criteria**:
- [ ] Administrators can drag-and-drop providers into a fallback order
- [ ] When a provider call fails (timeout or error), the system
  automatically retries with the next provider in the chain
- [ ] The system logs which provider was ultimately used for each
  agent turn
- [ ] If all providers in the chain fail, the swarm is terminated
  with an error comment posted to the task

### FR-7: Live Configuration Reload

**Priority**: Must
**Description**: Configuration changes MUST take effect for new swarm
tasks without restarting the daemon. Running swarms continue with their
original configuration.

**Acceptance Criteria**:
- [ ] New tasks started after a configuration change use the updated
  provider settings
- [ ] Currently running swarms are not interrupted by configuration
  changes
- [ ] The configuration is persisted and survives daemon restarts

### FR-8: Provider Status Dashboard

**Priority**: Should
**Description**: The dashboard SHOULD display the current connection
status of each configured provider (connected, disconnected, unknown)
and recent latency metrics.

**Acceptance Criteria**:
- [ ] Each provider card shows a status indicator (green/red/gray)
- [ ] Administrators can manually refresh the connection status
- [ ] Status reflects the result of the last successful or failed
  health check
- [ ] Average response time for the last 24 hours is displayed per
  provider

## Success Criteria

| Criterion                      | Measure                           | Target           |
|--------------------------------|-----------------------------------|------------------|
| Provider setup time            | Time to add a new provider and    | Under 2 minutes  |
|                                | validate credentials              |                  |
| Configuration propagation      | Time from save to new tasks       | Under 30 seconds |
|                                | using updated settings            |                  |
| Credential safety              | Credentials visible in full after | Never            |
|                                | initial entry                     |                  |
| Fallback reliability           | Percentage of provider failures   | 100% coverage    |
|                                | that trigger a successful fallback|                  |
| Dashboard responsiveness       | Time for status change to appear  | Under 10 seconds |
|                                | on the dashboard                  |                  |

## Key Entities

| Entity              | Description                              | Key Attributes                       |
|---------------------|------------------------------------------|--------------------------------------|
| Provider            | A language model service configuration   | id, name, type, endpoint_url,       |
|                     |                                          | credentials (encrypted), status,     |
|                     |                                          | default_model                        |
| Provider Type       | Category of provider (direct,           | type_key, required_fields,           |
|                     | aggregator, self-hosted)                 | optional_fields                      |
| Role Model Mapping  | Assignment of provider + model to an     | role_name, provider_id, model_name,  |
|                     | specific agent role                     | is_override                          |
| Fallback Chain      | Ordered list of providers to try when    | provider_id, position,               |
|                     | the primary fails                        | max_retries, timeout_seconds         |

## Assumptions

- Each provider type has a well-known set of required fields; the
  dashboard dynamically shows or hides fields based on the selected type
- Self-hosted providers expose a compatible API endpoint on the
  network reachable from the VPS
- Credential storage uses symmetric encryption at rest; the encryption
  key is stored in an environment variable, not in the database
- The initial version supports exactly three provider types; adding more
  types requires a code change but not a schema change
- Provider health checks run on a periodic schedule (every 5 minutes)
  and also on-demand when an administrator requests a refresh
- The global default provider is used for any agent role that does not
  have a per-role override
- Fallback order is a simple priority list; no weighted routing or
  load balancing between providers in the initial version

## Out of Scope

- Weighted load balancing across providers (round-robin, cost-based)
- Token usage or cost tracking per provider
- Automatic provider provisioning or account creation
- Rate limiting or quota management per provider
- Multi-tenant provider configuration (different teams with different
  providers)
- Streaming or partial response handling differences between providers

## Constitution Compliance

| Principle           | Compliance                                                              |
|---------------------|-------------------------------------------------------------------------|
| Clarity First       | Provider types have clear, distinct field requirements; role           |
|                     | assignments are explicit with visible overrides; fallback order is      |
|                     | transparent                                                             |
| Test-Driven         | Every FR has measurable acceptance criteria; credential validation      |
|                     | is tested before saving; fallback reliability is tracked                 |
| Modular Architecture| Provider configuration is a separate concern from swarm orchestration;  |
|                     | adding a new provider type does not require changes to agent logic      |
| Security by Default | Credentials are encrypted at rest; never shown in full after entry;      |
|                     | validation prevents invalid credentials from being stored               |
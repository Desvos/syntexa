# Feature Specification: Agent Swarm Platform

**Short Name**: agent-swarm-platform
**Status**: Draft
**Created**: 2026-04-14
**Author**: antoniodevivo

## Overview

Syntexa is an autonomous coding platform that runs 24/7 on a VPS. It
polls a project management tool for development tasks, assembles a team
of AI agents (a "swarm") for each task, and the agents collaborate to
plan, implement, test, review, and deliver code changes as pull
requests. Users manage agent roles, swarm compositions, and system
settings through a web dashboard.

The platform eliminates manual delegation of routine coding tasks. A
human operator tags a task, and the swarm handles the rest — from
analysis to pull request — while keeping the human in the loop via
status updates and review gates.

## User Scenarios & Testing

### Primary Scenario

**As a** project lead,
**I want** to tag a development task so that an agent swarm picks it up
and delivers a pull request,
**So that** routine coding work progresses without manual delegation.

**Steps**:
1. User tags a task in the project management tool with an
   agent-trigger tag (e.g., "ag2-agent")
2. The daemon detects the tagged task within the next polling cycle
3. The daemon creates an isolated workspace (branch) for the task
4. A swarm of agents is assembled based on the task type
5. Agents collaborate: planner analyzes, coder implements, tester
   verifies, reviewer approves
6. A pull request is created and linked back to the task
7. The task status is updated to indicate review is needed

### Alternative Scenarios

| Scenario              | Condition                           | Expected Outcome                        |
|-----------------------|-------------------------------------|-----------------------------------------|
| Bug fix task          | Task title or tag contains "fix"    | Swarm skips planner; coder starts       |
| immediately          |                                     |                                         |
| Refactoring task      | Task type is "refactor"            | Swarm includes two coders for parallel  |
|                       |                                     | work                                    |
| Task fails mid-swarm  | Agent encounters an unresolvable   | Error is logged, task status reverts,   |
|                       | error                               | comment with failure details is added   |
| Max swarms reached    | All swarm slots are occupied        | New tasks wait in queue until a slot    |
|                       |                                     | frees up                                |
| Custom role assigned  | User creates a "security-auditor"   | New swarm composition includes the      |
|                       | role via dashboard                  | custom role when matching task type     |

### Edge Cases

| Edge Case               | Trigger                          | Handling                              |
|-------------------------|----------------------------------|---------------------------------------|
| Duplicate task pickup   | Task already being processed     | System skips tasks in the active set  |
| Empty task description  | Task has no description field   | Swarm proceeds with task name only;   |
|                         |                                  | planner notes missing context         |
| Polling failure         | Project management API           | Error logged, retry on next cycle;    |
|                         | returns error                    | existing swarms continue running      |
| PR creation failure     | Git push or PR API fails         | Error logged, task status reverts,    |
|                         |                                  | failure comment posted                |
| Long-running task       | Swarm exceeds max conversation   | Swarm terminates gracefully, task      |
|                         | rounds                           | marked with timeout comment           |

## Functional Requirements

### FR-1: Task Polling

**Priority**: Must
**Description**: The system MUST periodically poll the project
management tool for tasks tagged with the agent-trigger tag and
status "in progress."

**Acceptance Criteria**:
- [ ] Tasks with the agent-trigger tag and "in progress" status are
  detected within one polling interval
- [ ] Already-active tasks are not picked up a second time
- [ ] Polling failures do not disrupt running swarms

### FR-2: Task Type Detection

**Priority**: Must
**Description**: The system MUST classify each task by type (feature,
fix, refactor, security, chore) based on task title or tags, with a
default of "feature."

**Acceptance Criteria**:
- [ ] Tasks containing "fix", "refactor", "security", or "chore" in
  title or tags are classified accordingly
- [ ] Tasks without a matching keyword default to "feature"
- [ ] Custom task types defined by the user are recognized (see FR-7)

### FR-3: Swarm Assembly

**Priority**: Must
**Description**: The system MUST assemble a team of agents for each
task, selected based on the task type. Agents MUST be able to
communicate with each other and hand off control.

**Acceptance Criteria**:
- [ ] Each task type maps to a defined agent composition
- [ ] Agents can pass control to one another during execution
- [ ] The swarm has a clear entry point (first agent) and exit
  condition (final agent commits or terminates)
- [ ] Context (task details, workspace path, branch name) is shared
  across all agents in the swarm

### FR-4: Agent Collaboration

**Priority**: Must
**Description**: Agents within a swarm MUST communicate through
structured handoffs. Each agent MUST have a defined role, a system
prompt describing its responsibility, and the ability to delegate to
other agents.

**Acceptance Criteria**:
- [ ] Each agent has a unique role name and responsibility description
- [ ] Agents can invoke handoff functions to transfer control
- [ ] The conversation history is available to all agents in the
  swarm
- [ ] Agents can execute shell commands within their isolated workspace

### FR-5: Isolated Workspace

**Priority**: Must
**Description**: Each swarm MUST operate in an isolated workspace
(branch) so that concurrent tasks do not interfere with each other.

**Acceptance Criteria**:
- [ ] A new branch is created for each task from the base branch
- [ ] No two swarms share the same branch
- [ ] The workspace is cleaned up after the task completes or fails

### FR-6: Pull Request Delivery

**Priority**: Must
**Description**: Upon successful completion, the swarm MUST commit
changes, push the branch, and create a pull request. The task in the
project management tool MUST be updated with the PR link.

**Acceptance Criteria**:
- [ ] Changes are committed with a descriptive conventional commit
  message
- [ ] A pull request is created targeting the base branch
- [ ] The task status is updated to "review" (or equivalent)
- [ ] A comment with the PR link and summary is added to the task

### FR-7: Custom Agent Roles

**Priority**: Must
**Description**: Users MUST be able to create, edit, and delete custom
agent roles through the web dashboard. Each role defines the agent's
name, system prompt, and which other roles it can hand off to.

**Acceptance Criteria**:
- [ ] Users can create a new role with a unique name, system prompt,
  and handoff targets
- [ ] Users can edit an existing role's prompt and handoff targets
- [ ] Users can delete a custom role (with confirmation if it is
  used in any swarm composition)
- [ ] Default roles (planner, coder, tester, reviewer) cannot be
  deleted but can be edited

### FR-8: Swarm Composition Management

**Priority**: Must
**Description**: Users MUST be able to define which agent roles
compose a swarm for each task type, and the order in which they
operate.

**Acceptance Criteria**:
- [ ] Users can assign a list of roles to each task type
- [ ] The order of roles in the list determines the handoff chain
- [ ] Users can add custom task types with their own compositions
- [ ] Changes to compositions take effect for new tasks, not running
  swarms

### FR-9: System Settings Dashboard

**Priority**: Should
**Description**: The web dashboard MUST provide access to system-wide
settings: polling interval, max concurrent swarms, project management
connection details, and repository configuration.

**Acceptance Criteria**:
- [ ] Users can view and update the polling interval
- [ ] Users can view and update the max concurrent swarms limit
- [ ] Users can view (but not edit) connection status for the project
  management tool and repository
- [ ] Changes are persisted and take effect without restarting the
  daemon

### FR-10: Swarm Monitoring

**Priority**: Should
**Description**: Users MUST be able to view the status of active and
recently completed swarms from the dashboard, including which task
each swarm is handling and its current agent.

**Acceptance Criteria**:
- [ ] Dashboard shows all currently running swarms with task name and
  active agent
- [ ] Dashboard shows recently completed swarms (last 50) with
  outcome (success/failure) and PR link
- [ ] Users can view the conversation log of a completed swarm

### FR-11: Concurrency Control

**Priority**: Must
**Description**: The system MUST limit the number of concurrent swarms
to a configurable maximum and queue excess tasks.

**Acceptance Criteria**:
- [ ] No more than the configured maximum number of swarms run
  simultaneously
- [ ] Tasks exceeding the limit remain in the queue and are picked up
  when a slot frees
- [ ] The queue is processed in first-in-first-out order

## Success Criteria

| Criterion                      | Measure                          | Target          |
|--------------------------------|----------------------------------|-----------------|
| Task pickup latency            | Time from tag to swarm start     | Under 2 minutes |
| End-to-end task completion     | Time from pickup to PR creation   | Under 30 minutes|
|                                | for a standard feature task      |                 |
| Concurrent task throughput     | Number of tasks processed        | Configurable    |
|                                | simultaneously                   | (default 3)     |
| Swarm reliability              | Percentage of tasks that produce | Above 80%       |
|                                | a valid PR without manual fix    |                 |
| Role configuration time        | Time to create a new custom role | Under 2 minutes |
| Dashboard responsiveness       | Time for dashboard to reflect   | Under 5 seconds |
|                                | a swarm status change            |                 |

## Key Entities

| Entity            | Description                              | Key Attributes                     |
|-------------------|------------------------------------------|------------------------------------|
| Task              | A unit of work from the project          | id, name, description, type,      |
|                   | management tool                          | status, tags                       |
| Agent Role        | A reusable role definition for an        | name, system_prompt,              |
|                   | agent in a swarm                         | handoff_targets, is_default       |
| Swarm Composition| A mapping from task type to an ordered    | task_type, roles (ordered list),   |
|                   | list of agent roles                      | max_rounds                         |
| Swarm Instance    | A running swarm handling a specific task | task_id, status, active_agent,    |
|                   |                                          | branch, conversation_log,         |
|                   |                                          | pr_url, started_at, completed_at  |
| System Settings   | Global configuration for the platform     | poll_interval, max_concurrent,    |
|                   |                                          | repo_path, base_branch            |

## Assumptions

- The project management tool provides a REST API with task listing,
  status updates, and comments (ClickUp used as reference)
- The code repository is hosted on a platform that supports branch
  creation, push, and pull requests via API (GitHub used as reference)
- The VPS has sufficient resources for the configured max concurrent
  swarms; each swarm primarily uses API calls, not heavy local compute
- Users access the dashboard via a modern web browser on desktop
- Authentication for the dashboard uses a simple shared-secret or
  single-user approach suitable for a VPS deployment (not a
  multi-tenant SaaS)
- The daemon runs as a background service and restarts automatically
  on failure
- Agent model preferences (which model each role uses) are configured
  globally, not per-role, in the initial version

## Out of Scope

- Multi-tenant or SaaS deployment — single VPS, single user
- Mobile-native dashboard — web only
- Automatic merging of pull requests (human review required)
- Agent learning or memory across tasks (each swarm is stateless)
- Integration with project management tools other than ClickUp
- Integration with repository platforms other than GitHub
- Real-time push notifications (polling is sufficient for VPS use)
- Agent billing or cost tracking per task

## Constitution Compliance

| Principle           | Compliance                                                               |
|---------------------|--------------------------------------------------------------------------|
| Clarity First       | Each requirement has unambiguous acceptance criteria; role names and      |
|                     | prompts are user-defined and explicit; task types are clearly classified  |
| Test-Driven         | Every FR has measurable acceptance criteria; success criteria are        |
|                     | quantified; swarm reliability is a tracked metric                        |
| Modular Architecture| Agent roles are loosely coupled units; swarm compositions are            |
|                     | configurable; dashboard, daemon, and swarm engine are separate concerns  |
| Security by Default | API keys stored in environment variables, not code; workspaces isolated   |
|                     | per task; dashboard auth required; no secrets in logs or PR descriptions |
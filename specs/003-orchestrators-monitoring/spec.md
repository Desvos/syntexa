# Feature Specification: Orchestrators Monitoring

**Short Name**: orchestrators-monitoring
**Status**: Draft
**Created**: 2026-04-15
**Author**: antoniodevivo

## Overview

This feature provides comprehensive real-time visibility into the health, activity, and performance of the agent swarm orchestration system. Platform administrators and operators can monitor active swarm instances, track task progress from polling to PR delivery, observe orchestrator health across daemon workers, and diagnose bottlenecks or failures without examining log files. A live dashboard displays running tasks, agent conversations, orchestrator status, and historical swarm execution metrics.

**Note**: This specification is drafted for future development. Implementation should begin after completing **Spec 002 - LLM Provider Settings**.

## User Scenarios & Testing

### Primary Scenario

**As a** platform administrator,
**I want** to see a real-time view of all active swarm orchestrators and the tasks they are processing,
**So that** I can monitor system health, identify stuck tasks, and ensure coding work is progressing without manual inspection.

**Steps**:
1. Administrator opens the monitoring dashboard
2. The dashboard displays a list of active orchestrators with status indicators
3. Administrator sees current swarm instances and their associated tasks
4. Administrator clicks on a task to see agent conversation flow and current step
5. Dashboard shows real-time updates as agents progress through the workflow
6. Administrator can pause/resume or terminate a stuck swarm if needed

### Alternative Scenarios

| Scenario                     | Condition                            | Expected Outcome                         |
|------------------------------|--------------------------------------|------------------------------------------|
| View historical swarms       | Administrator selects date range     | Dashboard shows completed/failed swarms with metrics |
| Filter by task status        | Administrator filters "in_progress"  | Only active tasks are displayed          |
| Filter by agent role         | Administrator filters by "reviewer"  | Only swarms with that role are shown     |
| Alert on stuck task          | Task exceeds max_rounds or timeout | Dashboard shows alert, sends notification  |
| Orchestrator offline         | Daemon worker disconnects            | Status changes to "offline", tasks shown as orphaned |
| Export execution log         | Administrator clicks export          | JSON/csv download of swarm conversation history |
| Drill into agent step        | Administrator clicks conversation    | Full message history with tool calls shown |
| Live tail mode               | Real-time dashboard refresh          | Updates every 5 seconds without page reload |
| Multi-tenant filter            | Future multi-tenant setup          | Admin sees only their org's tasks (deferred) |
| Compare swarm performance    | Select baseline vs current swarm     | Metrics comparison side-by-side          |

### Edge Cases

| Edge Case                    | Trigger                            | Handling                                |
|------------------------------|------------------------------------|-----------------------------------------|
| Database connection lost     | Cannot read swarm status           | Dashboard shows "data unavailable" with last cache |
| Very long conversation       | >1000 messages in swarm            | Paginate conversation view with truncation warning |
| Parallel daemon instances    | Multiple daemon workers            | Aggregate view with worker breakdown   |
| Swarm terminated abnormally  | Process kill or crash              | Mark as "crashed", preserve partial log |
| Task deleted in ClickUp      | Task no longer exists              | Swarm continues but shows warning with task ID |
| High volume of swarms        | >100 concurrent tasks              | Implement pagination and filtering defaults |
| Session token expires        | Admin viewing long-running task    | Prompt re-login, preserve current view state |
| Browser disconnected           | Network interruption               | Auto-reconnect with buffer of updates    |

## Functional Requirements

### FR-1: Orchestrator Status Overview

**Priority**: Must
**Description**: The dashboard MUST display a real-time summary of all orchestrator instances (daemon workers) including their connection status, current load, and health metrics.

**Acceptance Criteria**:
- [ ] List shows all active daemon instances with identifier and version
- [ ] Each orchestrator shows status: online, offline, degraded, or maintenance
- [ ] Current load displayed as active swarm count vs max capacity
- [ ] Last heartbeat timestamp shown for each orchestrator
- [ ] Health check endpoint tested every 30 seconds
- [ ] Offline orchestrators trigger optional notification (email/webhook)

### FR-2: Active Swarm List

**Priority**: Must
**Description**: The dashboard MUST display all currently running swarm instances with task association, progress indicator, and estimated completion.

**Acceptance Criteria**:
- [ ] Swarms shown in card/list view with task ID, title, type
- [ ] Current step/agent displayed (e.g., "planner: analyzing requirements")
- [ ] Progress bar based on conversation rounds vs max_rounds
- [ ] Started timestamp and estimated duration
- [ ] Click to expand full conversation details
- [ ] Filters: by orchestrator, by task type, by status

### FR-3: Task Detail View

**Priority**: Must
**Description**: Administrators MUST be able to drill into any active or completed task to see full details including ClickUp link, branch, PR status, and agent conversation history.

**Acceptance Criteria**:
- [ ] Task metadata panel shows external references (ClickUp task ID, GitHub PR)
- [ ] Agent conversation displayed as chronological message flow
- [ ] Tool calls shown with arguments and results
- [ ] Handoff events highlighted between agent roles
- [ ] Failed tool calls clearly marked with error details
- [ ] Manual actions available: stop swarm, add comment, force handoff

### FR-4: Historical Swarm Access

**Priority**: Should
**Description**: The dashboard SHOULD provide searchable access to completed and failed swarm executions with filtering by date range, task type, and outcome.

**Acceptance Criteria**:
- [ ] Date range selector defaults to last 7 days
- [ ] Filter by outcome: success, failed, terminated, timeout
- [ ] Search by task title or task ID
- [ ] Sort by start time, duration, or task type
- [ ] Export selected swarm execution as JSON
- [ ] Archive old executions after configurable retention (default 90 days)

### FR-5: Real-Time Metrics

**Priority**: Should
**Description**: The dashboard SHOULD display aggregate performance metrics including throughput, latency, success rate, and agent utilization.

**Acceptance Criteria**:
- [ ] Swarms per hour/day chart
- [ ] Average completion time by task type
- [ ] Success rate percentage with trend
- [ ] Agent utilization: time each role spends on tasks
- [ ] Queue depth: pending tasks waiting for swarm slot
- [ ] Provider usage stats (calls per provider/model)
- [ ] All metrics refresh every 60 seconds

### FR-6: Alert Configuration

**Priority**: Should
**Description**: Administrators SHOULD be able to configure alert rules for conditions like stuck tasks, failed swarms, or orchestrator disconnections.

**Acceptance Criteria**:
- [ ] Alert rules: stuck threshold (minutes), consecutive failures
- [ ] Notification channels: dashboard banner, email, webhook, Slack
- [ ] Alert severity levels: info, warning, critical
- [ ] Mute/snooze functionality per alert
- [ ] Alert history view with resolution status
- [ ] Acknowledge/dismiss actions per alert

### FR-7: Live Log Streaming

**Priority**: Could
**Description**: The dashboard COULD provide live streaming of agent conversation updates without requiring page refresh for active monitoring.

**Acceptance Criteria**:
- [ ] WebSocket or Server-Sent Events for live updates
- [ ] Smooth append of new messages to conversation view
- [ ] Optional sound notification on handoff
- [ ] Pause/resume streaming controls
- [ ] Reconnection handling with missed event catchup

### FR-8: Orchestrator Control Actions

**Priority**: Should
**Description**: Administrators SHOULD be able to control orchestrator behavior including pausing new task pickup, draining for maintenance, and graceful shutdown.

**Acceptance Criteria**:
- [ ] Pause: stop accepting new tasks, finish active swarms
- [ ] Drain: finish all swarms then go offline
- [ ] Resume: return to normal operation
- [ ] Terminate swarm: force stop with optional comment
- [ ] Scale up/down: signal orchestrator to adjust worker threads
- [ ] All actions logged with administrator attribution

## Success Criteria

| Criterion                      | Measure                           | Target           |
|-------------------------------|-----------------------------------|------------------|
| Dashboard load time           | Time from click to first render   | Under 3 seconds  |
| Real-time update latency      | Time from event to display        | Under 5 seconds  |
| Historical search speed       | Time to filter 1000 swarms        | Under 2 seconds  |
| Alert delivery time           | Time from trigger to notification | Under 30 seconds |
| Export generation             | Time for 500-swarm export         | Under 10 seconds |
| Metric accuracy               | Delta vs backend logs             | 99% match        |
| Uptime visibility             | % of time dashboard shows true    | 99.5% accurate   |

## Key Entities

| Entity              | Description                              | Key Attributes                       |
|---------------------|------------------------------------------|--------------------------------------|
| Orchestrator        | Daemon worker instance                   | id, hostname, version, status, started_at, last_heartbeat, max_capacity, active_swarms |
| Swarm Session       | Running or completed agent swarm         | id, task_ref, composition_id, status, started_at, ended_at, rounds_used, outcome, conversation_log |
| Task Execution      | Link between external task and swarm     | id, external_task_id, branch_name, pr_url, created_at, updated_at |
| Monitoring Event    | Discrete event for timeline/alerts       | id, swarm_id, event_type, severity, message, timestamp, resolved_at |
| Alert Rule          | Configured alert conditions              | id, name, condition_type, threshold, notification_channels, enabled, created_by |
| Metric Snapshot     | Periodic capture of aggregates           | id, timestamp, swarms_active, swarms_completed, avg_duration, success_rate, queue_depth |

## Assumptions

- Monitoring data is stored in the same SQLite database as configuration, partitioned by date for performance
- Conversation logs are truncated after 10,000 messages to prevent storage bloat
- Heartbeat mechanism uses HTTP health check endpoint from dashboard to daemon API
- WebSocket fallback to polling every 10 seconds if real-time connection fails
- Only one monitoring dashboard instance expected (no multi-user concurrency concerns initially)
- Alert notifications use existing SMTP/webhook configuration from system settings
- Metric retention: 90 days for detailed logs, 1 year for aggregates
- Dashboard queries are optimized with database indexes on task_id, started_at, and status fields

## Out of Scope

- Distributed tracing across agent boundaries
- Cost analysis or billing per task/provider
- Resource usage metrics (CPU, memory, disk) of daemon instances
- Comparative A/B testing of different swarm compositions
- Automatic anomaly detection (ML-based)
- Multi-region orchestrator federation
- Mobile-optimized monitoring view

## Constitution Compliance

| Principle           | Compliance                                                              |
|---------------------|-------------------------------------------------------------------------|
| Clarity First       | Status indicators use standard colors; progress clearly communicated; errors surface user- actionable details |
| Test-Driven         | Every FR has measurable targets; monitoring accuracy validated against ground truth logs |
| Modular Architecture| Monitoring is additive layer on existing swarm execution; no changes to core orchestration required |
| Security by Default | Task data access requires same auth as management dashboard; actions logged for audit |

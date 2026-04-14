import React from 'react';

export default function ActiveSwarms({ swarms, loading, onRefresh }) {
  if (loading) {
    return <p className="muted">Loading active swarms...</p>;
  }

  if (!swarms || swarms.length === 0) {
    return (
      <div className="empty-state">
        <p className="muted">No active swarms.</p>
        <p className="hint">Tag a task in ClickUp to start a swarm.</p>
      </div>
    );
  }

  const formatDuration = (startedAt) => {
    const start = new Date(startedAt);
    const now = new Date();
    const diffMs = now - start;
    const diffMins = Math.floor(diffMs / 60000);
    const hours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;

    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  return (
    <div className="swarms-table-container">
      <div className="table-header">
        <h3>Active Swarms ({swarms.length})</h3>
        <button onClick={onRefresh} className="secondary" disabled={loading}>
          Refresh
        </button>
      </div>

      <table className="swarms-table">
        <thead>
          <tr>
            <th>Task</th>
            <th>Type</th>
            <th>Active Agent</th>
            <th>Branch</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          {swarms.map((swarm) => (
            <tr key={swarm.id}>
              <td>
                <div className="task-cell">
                  <span className="task-name">{swarm.task_name}</span>
                  <span className="task-id">{swarm.task_id}</span>
                </div>
              </td>
              <td>
                <span className={`badge type-${swarm.task_type}`}>
                  {swarm.task_type}
                </span>
              </td>
              <td>
                <span className="agent-badge">{swarm.active_agent || '—'}</span>
              </td>
              <td>
                <code className="branch-name">{swarm.branch}</code>
              </td>
              <td>
                <span className="duration">{formatDuration(swarm.started_at)}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

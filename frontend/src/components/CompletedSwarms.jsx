import React from 'react';

export default function CompletedSwarms({ swarms, loading, onViewLog, selectedSwarmId }) {
  if (loading) {
    return <p className="muted">Loading completed swarms...</p>;
  }

  if (!swarms || swarms.length === 0) {
    return (
      <div className="empty-state">
        <p className="muted">No completed swarms yet.</p>
      </div>
    );
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      case 'timeout':
        return '⏱️';
      default:
        return '❓';
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'completed':
        return 'status-completed';
      case 'failed':
        return 'status-failed';
      case 'timeout':
        return 'status-timeout';
      default:
        return '';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatDuration = (startedAt, completedAt) => {
    if (!completedAt) return '—';
    const start = new Date(startedAt);
    const end = new Date(completedAt);
    const diffMs = end - start;
    const diffMins = Math.floor(diffMs / 60000);
    const hours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;
    const secs = Math.floor((diffMs % 60000) / 1000);

    if (hours > 0) {
      return `${hours}h ${mins}m ${secs}s`;
    }
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="swarms-table-container">
      <h3>Completed Swarms ({swarms.length} shown)</h3>

      <table className="swarms-table">
        <thead>
          <tr>
            <th>Status</th>
            <th>Task</th>
            <th>Type</th>
            <th>Duration</th>
            <th>Completed</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {swarms.map((swarm) => (
            <tr
              key={swarm.id}
              className={selectedSwarmId === swarm.id ? 'selected' : ''}
            >
              <td>
                <span
                  className={`status-badge ${getStatusClass(swarm.status)}`}
                  title={swarm.status}
                >
                  {getStatusIcon(swarm.status)} {swarm.status}
                </span>
              </td>
              <td>
                <div className="task-cell">
                  <span className="task-name">{swarm.task_name}</span>
                  {swarm.pr_url && (
                    <a
                      href={swarm.pr_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="pr-link"
                    >
                      View PR →
                    </a>
                  )}
                </div>
              </td>
              <td>
                <span className={`badge type-${swarm.task_type}`}>
                  {swarm.task_type}
                </span>
              </td>
              <td>{formatDuration(swarm.started_at, swarm.completed_at)}</td>
              <td>{formatDate(swarm.completed_at)}</td>
              <td>
                <button
                  onClick={() => onViewLog(swarm.id)}
                  className="secondary small"
                  disabled={selectedSwarmId === swarm.id}
                >
                  {selectedSwarmId === swarm.id ? 'Viewing...' : 'View Log'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

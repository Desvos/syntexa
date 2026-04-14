import React from 'react';

export default function ConnectionStatus({ connections }) {
  if (!connections || connections.length === 0) {
    return (<p className="muted">No connection data available.</p>);
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected':
        return '✅';
      case 'error':
        return '❌';
      case 'unconfigured':
        return '⚠️';
      default:
        return '❓';
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'connected':
        return 'status-connected';
      case 'error':
        return 'status-error';
      case 'unconfigured':
        return 'status-warning';
      default:
        return '';
    }
  };

  return (
    <div className="connection-status">
      <h3>Connection Status</h3>
      <div className="connections-grid">
        {connections.map((conn) => (
          <div
            key={conn.service}
            className={`connection-card ${getStatusClass(conn.status)}`}
          >
            <div className="connection-header">
              <span className="status-icon">{getStatusIcon(conn.status)}</span>
              <span className="service-name">{conn.service.toUpperCase()}</span>
            </div>
            <div className="connection-details">
              <span className={`status-badge ${getStatusClass(conn.status)}`}>
                {conn.status}
              </span>
              {conn.message && (
                <p className="status-message">{conn.message}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

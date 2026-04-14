import React from 'react';

export default function LogViewer({ logData, loading, onClose }) {
  if (!logData && !loading) return null;

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

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="log-viewer-overlay">
      <div className="log-viewer">
        <div className="log-viewer-header">
          <div className="log-viewer-title">
            {loading ? (
              <>Loading log...</>
            ) : (
              <>
                <span>{getStatusIcon(logData.status)}</span>
                <span>{logData.task_name}</span>
                <span className="status-badge">{logData.status}</span>
              </>
            )}
          </div>
          <button onClick={onClose} className="close-button">✕</button>
        </div>

        {loading ? (
          <div className="log-viewer-content">
            <p className="muted">Loading conversation log...</p>
          </div>
        ) : (
          <>
            <div className="log-viewer-meta">
              <dl>
                <dt>Task ID:</dt>
                <dd>{logData.task_id}</dd>

                <dt>Status:</dt>
                <dd>{logData.status}</dd>

                <dt>Started:</dt>
                <dd>{formatDate(logData.started_at)}</dd>

                {logData.completed_at && (
                  <>
                    <dt>Completed:</dt>
                    <dd>{formatDate(logData.completed_at)}</dd>
                  </>
                )}

                {logData.pr_url && (
                  <>
                    <dt>PR URL:</dt>
                    <dd>
                      <a href={logData.pr_url} target="_blank" rel="noopener noreferrer">
                        {logData.pr_url}
                      </a>
                    </dd>
                  </>
                )}
              </dl>
            </div>

            <div className="log-viewer-content">
              <h4>Conversation Log</h4>
              {logData.log ? (
                <pre className="log-content">{logData.log}</pre>
              ) : (
                <p className="muted">
                  No conversation log available.
                  {logData.status === 'running' && ' Swarm is still active.'}
                  {(logData.status === 'completed' || logData.status === 'failed') &&
                    ' Log may have been cleaned up due to retention policy.'}
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

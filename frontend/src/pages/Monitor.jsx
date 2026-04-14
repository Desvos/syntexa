import React, { useCallback, useEffect, useState } from 'react';

import { api, ApiError } from '../api/client.js';
import ActiveSwarms from '../components/ActiveSwarms.jsx';
import CompletedSwarms from '../components/CompletedSwarms.jsx';
import LogViewer from '../components/LogViewer.jsx';

export default function MonitorPage() {
  const [activeSwarms, setActiveSwarms] = useState([]);
  const [completedSwarms, setCompletedSwarms] = useState([]);
  const [loadingActive, setLoadingActive] = useState(true);
  const [loadingCompleted, setLoadingCompleted] = useState(true);
  const [error, setError] = useState(null);

  // Log viewer state
  const [selectedSwarmId, setSelectedSwarmId] = useState(null);
  const [logData, setLogData] = useState(null);
  const [loadingLog, setLoadingLog] = useState(false);

  const POLLING_INTERVAL = 5000; // 5 seconds

  const loadActiveSwarms = useCallback(async () => {
    try {
      const data = await api.swarms.active();
      setActiveSwarms(data.swarms);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load active swarms.');
      }
    } finally {
      setLoadingActive(false);
    }
  }, []);

  const loadCompletedSwarms = useCallback(async () => {
    try {
      const data = await api.swarms.completed(50);
      setCompletedSwarms(data.swarms);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load completed swarms.');
      }
    } finally {
      setLoadingCompleted(false);
    }
  }, []);

  const loadAll = useCallback(() => {
    setLoadingActive(true);
    setLoadingCompleted(true);
    setError(null);

    Promise.all([loadActiveSwarms(), loadCompletedSwarms()]).finally(() => {
      // Loading flags are handled by individual loaders
    });
  }, [loadActiveSwarms, loadCompletedSwarms]);

  const handleViewLog = async (swarmId) => {
    setSelectedSwarmId(swarmId);
    setLoadingLog(true);
    setLogData(null);

    try {
      const data = await api.swarms.log(swarmId);
      setLogData(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load swarm log.');
      }
      setSelectedSwarmId(null);
    } finally {
      setLoadingLog(false);
    }
  };

  const handleCloseLog = () => {
    setSelectedSwarmId(null);
    setLogData(null);
  };

  // Initial load and polling
  useEffect(() => {
    loadAll();

    // Set up polling for active swarms
    const interval = setInterval(loadActiveSwarms, POLLING_INTERVAL);

    return () => clearInterval(interval);
  }, [loadAll, loadActiveSwarms]);

  return (
    <main>
      <h1>Swarm Monitor</h1>
      <p className="muted">
        Monitor active and completed swarm instances. Active swarms update every {POLLING_INTERVAL / 1000}s.
      </p>

      {error && <div className="error" role="alert">{error}</div>}

      <section aria-label="active swarms">
        <ActiveSwarms
          swarms={activeSwarms}
          loading={loadingActive}
          onRefresh={loadActiveSwarms}
        />
      </section>

      <section aria-label="completed swarms">
        <CompletedSwarms
          swarms={completedSwarms}
          loading={loadingCompleted}
          onViewLog={handleViewLog}
          selectedSwarmId={selectedSwarmId}
        />
      </section>

      <LogViewer
        logData={logData}
        loading={loadingLog}
        onClose={handleCloseLog}
      />

      <div className="monitor-actions">
        <button onClick={loadAll} className="secondary">
          Refresh All
        </button>
      </div>
    </main>
  );
}

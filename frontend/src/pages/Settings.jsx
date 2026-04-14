import React, { useCallback, useEffect, useState } from 'react';

import { api, ApiError } from '../api/client.js';
import ConnectionStatus from '../components/ConnectionStatus.jsx';

const DEFAULT_SETTINGS = {
  poll_interval: 300,
  max_concurrent: 3,
  log_retention_days: 30,
  agent_trigger_tag: 'agent-swarm',
  base_branch: 'main',
  repo_path: '.',
};

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [originalSettings, setOriginalSettings] = useState(null);
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);

  const loadSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [settingsData, statusData] = await Promise.all([
        api.settings.get(),
        api.settings.status(),
      ]);
      setSettings(settingsData);
      setOriginalSettings(settingsData);
      setConnections(statusData.connections);
      setHasChanges(false);
    } catch (err) {
      setError(err.message || 'Failed to load settings.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const handleChange = (key, value) => {
    setSettings((prev) => {
      const updated = { ...prev, [key]: value };
      setHasChanges(JSON.stringify(updated) !== JSON.stringify(originalSettings));
      return updated;
    });
    setError(null);
    setSuccess(null);
  };

  const handleSave = async () => {
    setError(null);
    setSuccess(null);

    try {
      // Build payload with only changed values
      const payload = {};
      Object.keys(DEFAULT_SETTINGS).forEach((key) => {
        if (settings[key] !== originalSettings[key]) {
          payload[key] = settings[key];
        }
      });

      if (Object.keys(payload).length === 0) {
        setSuccess('No changes to save.');
        return;
      }

      const updated = await api.settings.update(payload);
      setSettings(updated);
      setOriginalSettings(updated);
      setHasChanges(false);
      setSuccess('Settings saved successfully. Changes take effect immediately.');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to save settings. Please try again.');
      }
    }
  };

  const handleReset = () => {
    setSettings(originalSettings);
    setHasChanges(false);
    setError(null);
    setSuccess(null);
  };

  const formatLabel = (key) => {
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const getSettingDescription = (key) => {
    const descriptions = {
      poll_interval: 'Seconds between ClickUp task polls (minimum 10)',
      max_concurrent: 'Maximum number of swarms running simultaneously (minimum 1)',
      log_retention_days: 'Days to retain completed swarm logs (minimum 1)',
      agent_trigger_tag: 'Tag that triggers swarm execution on tasks',
      base_branch: 'Git branch to create PRs from',
      repo_path: 'Local path to the repository (read-only)',
    };
    return descriptions[key] || '';
  };

  const renderSettingInput = (key, value) => {
    const isNumeric = typeof DEFAULT_SETTINGS[key] === 'number';

    if (key === 'repo_path') {
      return (
        <input
          type="text"
          id={key}
          value={value}
          disabled
          className="input-disabled"
        />
      );
    }

    return (
      <input
        type={isNumeric ? 'number' : 'text'}
        id={key}
        value={value}
        onChange={(e) => handleChange(key, isNumeric ? parseInt(e.target.value, 10) || 0 : e.target.value)}
        min={isNumeric ? 1 : undefined}
        className="input"
      />
    );
  };

  if (loading && !settings) {
    return (
      <main>
        <h1>System Settings</h1>
        <p className="muted">Loading...</p>
      </main>
    );
  }

  return (
    <main>
      <h1>System Settings</h1>
      <p className="muted">
        Configure daemon behavior. Runtime-tunable settings take effect without restart.
      </p>

      {error && <div className="error" role="alert">{error}</div>}
      {success && <div className="success" role="status">{success}</div>}

      <section aria-label="settings form">
        <div className="settings-form">
          {Object.keys(DEFAULT_SETTINGS).map((key) => (
            <div key={key} className="form-group">
              <label htmlFor={key}>{formatLabel(key)}</label>
              {renderSettingInput(key, settings?.[key] ?? DEFAULT_SETTINGS[key])}
              <p className="help-text">{getSettingDescription(key)}</p>
            </div>
          ))}
        </div>

        <div className="form-actions">
          <button
            className="primary"
            onClick={handleSave}
            disabled={!hasChanges || loading}
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
          <button
            onClick={handleReset}
            disabled={!hasChanges || loading}
            className="secondary"
          >
            Reset
          </button>
        </div>
      </section>

      <section aria-label="connection status">
        <ConnectionStatus connections={connections} />
      </section>
    </main>
  );
}

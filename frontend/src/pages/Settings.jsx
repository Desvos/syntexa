import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Divider,
  Grid,
  Skeleton,
  Slider,
  Snackbar,
  TextField,
  Typography,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import RefreshIcon from '@mui/icons-material/Refresh';
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

/**
 * SettingsPage - System settings page with MUI components
 *
 * Features:
 * - Form fields with validation
 * - Slider for numeric settings
 * - Save/Reset actions
 * - Connection status display
 * - Snackbar notifications
 */
export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [originalSettings, setOriginalSettings] = useState(null);
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
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
  };

  const handleSave = async () => {
    setError(null);
    setSaving(true);

    try {
      const payload = {};
      Object.keys(DEFAULT_SETTINGS).forEach((key) => {
        if (settings[key] !== originalSettings[key]) {
          payload[key] = settings[key];
        }
      });

      if (Object.keys(payload).length === 0) {
        setSnackbar({ open: true, message: 'No changes to save.', severity: 'info' });
        setSaving(false);
        return;
      }

      const updated = await api.settings.update(payload);
      setSettings(updated);
      setOriginalSettings(updated);
      setHasChanges(false);
      setSnackbar({ open: true, message: 'Settings saved successfully. Changes take effect immediately.', severity: 'success' });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to save settings. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setSettings(originalSettings);
    setHasChanges(false);
    setError(null);
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
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

  const getSliderConfig = (key) => {
    const configs = {
      poll_interval: { min: 10, max: 3600, step: 10 },
      max_concurrent: { min: 1, max: 10, step: 1 },
      log_retention_days: { min: 1, max: 365, step: 1 },
    };
    return configs[key] || { min: 0, max: 100, step: 1 };
  };

  if (loading && !settings) {
    return (
      <Box sx={{ width: '100%' }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 500, mb: 2 }}>
          System Settings
        </Typography>
        <Skeleton variant="rectangular" height={400} />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" component="h1" sx={{ fontWeight: 500, mb: 1 }}>
        System Settings
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure daemon behavior. Runtime-tunable settings take effect without restart.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card variant="outlined">
            <CardHeader
              title="Daemon Configuration"
              action={
                <Button
                  startIcon={<RefreshIcon />}
                  onClick={loadSettings}
                  disabled={loading}
                  size="small"
                >
                  Refresh
                </Button>
              }
            />
            <CardContent>
              <Grid container spacing={3}>
                {Object.keys(DEFAULT_SETTINGS).map((key) => {
                  const isNumeric = typeof DEFAULT_SETTINGS[key] === 'number';
                  const isReadOnly = key === 'repo_path';
                  const sliderConfig = isNumeric ? getSliderConfig(key) : null;

                  return (
                    <Grid item xs={12} key={key}>
                      {isNumeric ? (
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>
                            {formatLabel(key)}
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, px: 1 }}>
                            <Slider
                              value={settings?.[key] ?? DEFAULT_SETTINGS[key]}
                              onChange={(e, v) => handleChange(key, v)}
                              disabled={loading || saving}
                              min={sliderConfig.min}
                              max={sliderConfig.max}
                              step={sliderConfig.step}
                              valueLabelDisplay="auto"
                              sx={{ flex: 1 }}
                            />
                            <TextField
                              type="number"
                              value={settings?.[key] ?? DEFAULT_SETTINGS[key]}
                              onChange={(e) => handleChange(key, parseInt(e.target.value) || sliderConfig.min)}
                              disabled={loading || saving}
                              inputProps={{ min: sliderConfig.min, max: sliderConfig.max }}
                              sx={{ width: 100 }}
                              size="small"
                            />
                          </Box>
                          <Typography variant="caption" color="text.secondary">
                            {getSettingDescription(key)}
                          </Typography>
                        </Box>
                      ) : (
                        <TextField
                          fullWidth
                          id={key}
                          label={formatLabel(key)}
                          value={settings?.[key] ?? DEFAULT_SETTINGS[key]}
                          onChange={(e) => handleChange(key, e.target.value)}
                          disabled={loading || saving || isReadOnly}
                          helperText={getSettingDescription(key)}
                          InputProps={{
                            readOnly: isReadOnly,
                          }}
                        />
                      )}
                    </Grid>
                  );
                })}
              </Grid>

              <Divider sx={{ my: 3 }} />

              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  onClick={handleReset}
                  disabled={!hasChanges || saving}
                >
                  Reset
                </Button>
                <Button
                  variant="contained"
                  startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
                  onClick={handleSave}
                  disabled={!hasChanges || saving}
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <ConnectionStatus connections={connections} loading={loading} />
        </Grid>
      </Grid>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} variant="filled">
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

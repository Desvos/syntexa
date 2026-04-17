import React, { useCallback, useEffect, useState, memo } from 'react';
import {
  Alert,
  Box,
  Button,
  Container,
  Typography,
  Snackbar,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { api, ApiError } from '../api/client.js';
import ActiveSwarms from '../components/ActiveSwarms.jsx';
import CompletedSwarms from '../components/CompletedSwarms.jsx';
import LogViewer from '../components/LogViewer.jsx';

/**
 * MonitorPage - Swarm monitoring dashboard with MUI components
 *
 * Features:
 * - Auto-polling every 5 seconds for active swarms
 * - Manual refresh for completed swarms
 * - Log viewer dialog
 * - Error handling with Snackbar (Vercel best practice: no inline error banners)
 */
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

  // Vercel best practice: useCallback for stable function references
  const loadActiveSwarms = useCallback(async () => {
    try {
      const data = await api.swarms.active();
      setActiveSwarms(data.swarms);
    } catch (err) {
      // Don't set error here - polling shouldn't show error on every failure
      console.error('Failed to load active swarms:', err);
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

    Promise.all([loadActiveSwarms(), loadCompletedSwarms()]);
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

  const handleCloseError = () => {
    setError(null);
  };

  // Initial load and polling
  useEffect(() => {
    loadAll();

    // Set up polling for active swarms
    const interval = setInterval(loadActiveSwarms, POLLING_INTERVAL);

    return () => clearInterval(interval);
  }, [loadAll, loadActiveSwarms]);

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 500, mb: 1 }}>
          Swarm Monitor
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Monitor active and completed swarm instances. Active swarms update every {POLLING_INTERVAL / 1000}s.
        </Typography>
      </Box>

      {/* Refresh All Button - Vercel best practice: clear action button */}
      <Box sx={{ mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadAll}
          disabled={loadingActive || loadingCompleted}
        >
          Refresh All
        </Button>
      </Box>

      {/* Active Swarms Section */}
      <Box component="section" aria-label="active swarms" sx={{ mb: 4 }}>
        <ActiveSwarms
          swarms={activeSwarms}
          loading={loadingActive}
          onRefresh={loadActiveSwarms}
        />
      </Box>

      {/* Completed Swarms Section */}
      <Box component="section" aria-label="completed swarms" sx={{ mb: 4 }}>
        <CompletedSwarms
          swarms={completedSwarms}
          loading={loadingCompleted}
          onViewLog={handleViewLog}
          selectedSwarmId={selectedSwarmId}
        />
      </Box>

      {/* Log Viewer Dialog */}
      <LogViewer
        logData={logData}
        loading={loadingLog}
        onClose={handleCloseLog}
      />

      {/* Error Snackbar - Vercel best practice: transient notification vs persistent banner */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseError}
          severity="error"
          variant="filled"
          sx={{ width: '100%' }}
        >
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
}
